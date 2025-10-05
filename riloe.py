import argparse
import os
import sys

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

    # Verificar que a ruta existe
    if not os.path.exists(args.ruta):
        print(f"Erro: A ruta '{args.ruta}' non existe.")
        sys.exit(1)

    if not os.path.isdir(args.ruta):
        print(f"Erro: '{args.ruta}' non é un cartafol.")
        sys.exit(1)

    print(f"Ruta dos ficheiros: {args.ruta}")
    print(f"Número de ficheiros a procesar: {args.numero_ficheiros}")

if __name__ == "__main__":
    main()
