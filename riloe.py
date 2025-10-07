import argparse
import os
import sys
import re
import shutil
from datetime import datetime
from pathlib import Path
import markdown
from ebooklib import epub


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
    book = epub.EpubBook()
    book.set_identifier('riloe-' + datetime.now().strftime('%Y%m%d'))
    book.set_title('Ler ' + datetime.now().strftime('%d/%m/%Y'))
    book.add_author('RILOE - Read-it-Later on EPUB')

    spine = ['nav']
    chapters = []
    for i, (file, date, frontmatter, body) in enumerate(selected_files):
        title = frontmatter.get('title', file.stem)
        md = markdown.Markdown(extensions=['extra'])
        html_content = md.convert(body)

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
