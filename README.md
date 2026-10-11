# WebP Converter

A small command-line utility for converting WebP images to common formats. The
project provides:

- [`webp_converter.py`](webp_converter.py) for converting one file at a time.
- [`main.sh`](main.sh) for converting every WebP file directly inside a
  directory.

The Python converter uses Pillow and supports BMP, JPEG, PNG, TIFF, and TIF
output. Animated WebP files are converted using their first frame only.

## Requirements

- Python 3.9 or newer
- Pillow (pinned in [`requirements.txt`](requirements.txt))

The batch script can also use an installed `dwebp` command from libwebp or
ImageMagick (`magick` or `convert`). If none of those are available, it uses
the Python converter. On Windows, when the repository's `venv` exists,
`main.sh` checks `venv/Scripts/python.exe` before looking for `python` on
`PATH`.

## Installation

Clone the project and install its Python dependency:

```bash
git clone https://github.com/yetiki/webp-converter.git
cd webp-converter
python -m venv venv
```

Activate the virtual environment:

```bash
# Linux/macOS/Git Bash
source venv/bin/activate

# Windows PowerShell
.\venv\Scripts\Activate.ps1

# Windows Command Prompt
venv\Scripts\activate.bat
```

Then install Pillow:

```bash
python -m pip install -r requirements.txt
```

On Windows, `main.sh` must be run from Git Bash, WSL, or another Bash
environment. The Python script can be run directly from PowerShell or
Command Prompt.

## Single-file conversion

The input WebP path is positional and the output path is required with
`--output` (or `-o`). The output extension selects the format:

```bash
python webp_converter.py input.webp --output output.png
python webp_converter.py input.webp -o output.jpg
python webp_converter.py input.webp -o output.tiff
```

Supported output extensions are `.bmp`, `.jpeg`, `.jpg`, `.png`, `.tif`, and
`.tiff`. Parent directories for the output are created automatically.

### Options

| Option | Description |
| --- | --- |
| `-o`, `--output PATH` | Required output path, including its extension. |
| `-q`, `--quality 1-95` | JPEG quality; defaults to `90` and is ignored for other formats. |
| `--overwrite` | Replace an existing output file. Without it, conversion fails if the output exists. |
| `-h`, `--help` | Show command-line help. |

Examples:

```bash
# Use a lower JPEG quality
python webp_converter.py photo.webp --output photo.jpg --quality 80

# Replace an existing file
python webp_converter.py photo.webp --output photo.png --overwrite
```

When converting to JPEG, transparent pixels are composited onto a white
background because JPEG does not support transparency. Embedded ICC colour
profiles are preserved where the target format supports them.

## Batch conversion with `main.sh`

Convert all `.webp` files directly inside an input directory to PNG files in
an output directory:

```bash
./main.sh path/to/webp-images path/to/png-images
```

The output directory is created if it does not exist. Files in nested
directories are not included. Existing PNG files are skipped by default; use
`--force` (or `-f`) to replace them:

```bash
./main.sh --force path/to/webp-images path/to/png-images
```

The script prints a result for each file and a final count of converted,
skipped, and failed files. It exits with status `1` if any conversion fails
and `0` otherwise. Temporary output names are used during conversion so a
failed conversion does not leave a partial PNG at the destination.

Show all batch options with:

```bash
./main.sh --help
```

## Notes

- Input files must have a `.webp` extension for the Python CLI. The batch
  script matches `.webp` case-insensitively.
- Animated WebP files are intentionally reduced to their first frame.
- The Python CLI validates that the file contents are actually WebP data,
  not just that the filename ends in `.webp`.
