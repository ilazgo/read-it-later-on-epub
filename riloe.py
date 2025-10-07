import argparse
import os
import sys
import re
import shutil
import requests
import hashlib
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
from PIL import Image
import markdown
from ebooklib import epub


def download_image(url, images_folder):
    try:
        url_hash = hashlib.md5(url.encode()).hexdigest()
        parsed_url = urlparse(url)
        extension = Path(parsed_url.path).suffix or '.jpg'
        filename = f"{url_hash}{extension}"
        filepath = images_folder / filename

        if not filepath.exists():
            response = requests.get(url, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            response.raise_for_status()
            with open(filepath, 'wb') as f:
                f.write(response.content)

            try:
                with Image.open(filepath) as img:
                    max_size = (600, 800)
                    if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                        img.thumbnail(max_size, Image.Resampling.LANCZOS)
                        img.save(filepath, optimize=True, quality=85)
            except Exception as e:
                print(f"Non se puido optimizar a imaxe {filename}: {e}")

        return filename
    except Exception as e:
        print(f"Erro ao descargar a imaxe {url}: {e}")
        return None


def process_images_in_markdown(body, images_folder):
    image_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
    def replace_image(match):
        alt_text = match.group(1)
        image_url = match.group(2).strip()
        local_filename = download_image(image_url, images_folder)
        return f'![{alt_text}](images/{local_filename})'

    return re.sub(image_pattern, replace_image, body)


def add_images_to_epub(book, images_folder):
    if not images_folder.exists():
        return

    for image_file in images_folder.glob('*'):
        if image_file.is_file():
            try:
                with open(image_file, 'rb') as f:
                    image_content = f.read()
                extension = image_file.suffix.lower()
                mime_type = {
                    '.jpg': 'image/jpeg',
                    '.jpeg': 'image/jpeg',
                    '.png': 'image/png',
                    '.gif': 'image/gif',
                    '.webp': 'image/webp'
                }.get(extension, 'image/jpeg')

                img = epub.EpubImage()
                img.file_name = f'images/{image_file.name}'
                img.media_type = mime_type
                img.content = image_content

                book.add_item(img)
            except Exception as e:
                print(f"Erro ao engadir a imaxe {image_file.name} ao EPUB: {e}")


def parse_frontmatter(content):
    if not content.startswith('---'):
        return {}, content

    end_match = re.search(r'\n---\n', content)
    if not end_match:
        return {}, content

    frontmatter_text = content[3:end_match.start()]
    body_content = content[end_match.end():]

    frontmatter = {}
    for line in frontmatter_text.strip().split('\n'):
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip().strip('"')
            frontmatter[key] = value

    return frontmatter, body_content


def get_markdown_files_with_dates(path):
    files_with_date = []

    for file in Path(path).glob('*.md'):
        try:
            with open(file, 'r', encoding='utf-8') as f:
                content = f.read()

            frontmatter, body = parse_frontmatter(content)
            if 'date' in frontmatter:
                try:
                    date_str = frontmatter['date']
                    if '+' in date_str:
                        date_str = date_str.split('+')[0]
                    elif 'Z' in date_str:
                        date_str = date_str.replace('Z', '')

                    date_obj = datetime.fromisoformat(date_str)
                    files_with_date.append((file, date_obj, frontmatter, body))
                except ValueError as e:
                    print(f"Aviso: Non se puido parsear a data do ficheiro {file}: {e}")
                    continue
        except Exception as e:
            print(f"Erro ao ler o ficheiro {file}: {e}")
            continue

    return files_with_date


def create_epub_folder(base_path):
    epub_folder = Path(base_path) / 'epub'
    epub_folder.mkdir(exist_ok=True)
    return epub_folder


def create_epub(selected_files, epub_folder):
    images_folder = epub_folder / 'imaxes'
    images_folder.mkdir(exist_ok=True)

    book = epub.EpubBook()
    book.set_identifier('riloe-' + datetime.now().strftime('%Y%m%d'))
    book.set_title('Ler ' + datetime.now().strftime('%d/%m/%Y'))
    book.add_author('RILOE - Read-it-Later on EPUB')

    spine = ['nav']
    chapters = []
    for i, (file, date, frontmatter, body) in enumerate(selected_files):
        title = frontmatter.get('title', file.stem)
        processed_body = process_images_in_markdown(body, images_folder)
        md = markdown.Markdown(extensions=['extra'])
        html_content = md.convert(processed_body)

        chapter = epub.EpubHtml(
            title=title,
            file_name=f'chapter_{i+1}.xhtml'
        )

        chapter_html = f'''
        <html>
        <head>
            <title>{title}</title>
        </head>
        <body>
            <h1>{title}</h1>
            {html_content}
        </body>
        </html>
        '''

        chapter.content = chapter_html
        book.add_item(chapter)
        chapters.append(chapter)
        spine.append(chapter)

    add_images_to_epub(book, images_folder)
    book.toc = [(epub.Section('Artigos'), chapters)]
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = spine

    epub_filename = f"ler_{datetime.now().strftime('%Y%m%d')}.epub"
    epub_path = epub_folder / epub_filename

    epub.write_epub(str(epub_path), book, {})

    return epub_path


def main():
    parser = argparse.ArgumentParser(
        description="Converte ficheiros markdown en Obsidian a un EPUB. Os ficheiros teñen unha estrutura de etiquetas determinada.",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "ruta",
        help="Ruta do cartafol onde están os ficheiros markdown"
    )

    parser.add_argument(
        "-n", "--numero-ficheiros",
        type=int,
        default=10,
        help="Número de ficheiros a incluír no EPUB (por defecto: 10)"
    )

    args = parser.parse_args()

    if not os.path.exists(args.ruta):
        print(f"Erro: A ruta '{args.ruta}' non existe.")
        sys.exit(1)

    if not os.path.isdir(args.ruta):
        print(f"Erro: '{args.ruta}' non é un cartafol.")
        sys.exit(1)

    files_with_date = get_markdown_files_with_dates(args.ruta)
    if not files_with_date:
        print("Non se atoparon ficheiros markdown con etiqueta 'date'.")
        sys.exit(1)
    files_with_date.sort(key=lambda x: x[1])
    selected_files = files_with_date[:args.numero_ficheiros]

    epub_folder = create_epub_folder(args.ruta)

    moved_files = []
    for file, date, frontmatter, body in selected_files:
        filepath = epub_folder / file.name
        try:
            shutil.move(str(file), str(filepath))
            moved_files.append((filepath, date, frontmatter, body))
        except Exception as e:
            print(f"Erro ao mover {file}: {e}")

    try:
        epub_path = create_epub(moved_files, epub_folder)
    except Exception as e:
        print(f"Erro ao crear o EPUB: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
