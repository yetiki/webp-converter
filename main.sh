#!/usr/bin/env bash
#
# Convert every .webp file in a directory to PNG in a new directory.

set -euo pipefail

usage() {
    cat <<EOF
Usage: ${0##*/} [-f] INPUT_DIR OUTPUT_DIR

Convert all .webp files directly inside INPUT_DIR to .png files in OUTPUT_DIR.
OUTPUT_DIR is created if it does not exist. Subdirectories are not searched.

Options:
  -f, --force   Replace existing PNG files (default: skip them)
  -h, --help    Show this help message

Requires dwebp (libwebp), ImageMagick, or the project's Python/Pillow converter.
Animated files use their first frame.
EOF
}

die() {
    echo "Error: $*" >&2
    exit 1
}

force=false
positional=()

while (($# > 0)); do
    case $1 in
        -f | --force) force=true ;;
        -h | --help)
            usage
            exit 0
            ;;
        -*) usage >&2; die "unknown option: $1" ;;
        *) positional+=("$1") ;;
    esac
    shift
done

((${#positional[@]} == 2)) || { usage >&2; exit 1; }

input_dir=${positional[0]}
output_dir=${positional[1]}
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)

[[ -d $input_dir ]] || die "input directory does not exist: $input_dir"

if command -v dwebp >/dev/null 2>&1; then
    converter=dwebp
elif command -v magick >/dev/null 2>&1; then
    converter=magick
elif command -v convert >/dev/null 2>&1 &&
    convert -version 2>&1 | grep -q '^Version: ImageMagick'; then
    converter=convert
elif [[ -x $script_dir/venv/Scripts/python.exe ]]; then
    converter=python
    python_bin=$script_dir/venv/Scripts/python.exe
elif command -v python >/dev/null 2>&1; then
    converter=python
    python_bin=python
else
    die "no converter found. Install libwebp (dwebp), ImageMagick, or Python with Pillow."
fi

mkdir -p -- "$output_dir"

# Convert one file via a temporary name so a failure never leaves a partial PNG.
convert_one() {
    local src=$1 dest=$2 tmp="$2.part.png"

    case $converter in
        dwebp) dwebp -quiet "$src" -o "$tmp" ;;
        magick) magick "${src}[0]" "png:$tmp" ;;
        convert) convert "${src}[0]" "png:$tmp" ;;
        python) "$python_bin" "$script_dir/webp_converter.py" "$src" -o "$tmp" ;;
    esac || {
        rm -f -- "$tmp"
        return 1
    }

    mv -f -- "$tmp" "$dest"
}

converted=0
skipped=0
failed=0

while IFS= read -r -d '' src; do
    name=$(basename -- "$src")
    dest="$output_dir/${name%.*}.png"

    if [[ -e $dest && $force == false ]]; then
        echo "Skipped (exists): $dest"
        skipped=$((skipped + 1))
        continue
    fi

    if convert_one "$src" "$dest"; then
        echo "Converted: $src -> $dest"
        converted=$((converted + 1))
    else
        echo "Failed: $src" >&2
        failed=$((failed + 1))
    fi
done < <(find "$input_dir" -maxdepth 1 -type f -iname '*.webp' -print0 | sort -z)

total=$((converted + skipped + failed))

if ((total == 0)); then
    echo "No .webp files found in $input_dir"
    exit 0
fi

echo "Done: $converted converted, $skipped skipped, $failed failed."

((failed == 0)) || exit 1