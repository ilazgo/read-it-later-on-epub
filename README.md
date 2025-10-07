# RILOE (Read It Later On Epub)
Personal python script to convert various markdown files to one epub file.

Un script Python que converte ficheiros markdown de Obsidian a formato EPUB e opcionalmente pode envialos a un Kindle.  Este é un script persoal para pasar ao Kindle os artigos que gardo en Obsidian para ler despois. O script funciona en Linux e require Calibre para enviar ao Kindle o epub. Os ficheiros markdown deben ter unha etiqueta `date`.

## Uso

```bash
python riloe.py <ruta_markdowns> [-n numero] [--kindle ruta_kindle]
```
- `ruta_markdowns`: Ruta ao cartafol con ficheiros markdown de Obsidian (obrigatorio)
- `-n, --numero-ficheiros`: Número de ficheiros a incluír (por defecto: 10)
- `--kindle RUTA_KINDLE`: Converte a MOBI e copia ao Kindle na ruta especificada

## Contribucións

Este script está deseñado para un workflow específico con Obsidian + Kindle. As contribucións son benvidas para mellorar a funcionalidade ou engadir novos casos de uso.

