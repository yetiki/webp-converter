import argparse
import sys
from pathlib import Path

from PIL import Image

VALID_OUTPUT_FORMATS: tuple[str, ...] = (".bmp", ".jpeg", ".jpg", ".png", ".tif", ".tiff")
JPEG_EXTENSIONS: frozenset[str] = frozenset({".jpg", ".jpeg"})
DEFAULT_JPEG_QUALITY: int = 90
MIN_JPEG_QUALITY: int = 1
MAX_JPEG_QUALITY: int = 95


def build_arg_parser() -> argparse.ArgumentParser:
    """
    Construct the argument parser for the command line interface.

    Returns
    -------
    argparse.ArgumentParser
        The constructed argument parser.
    """
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description=(
            "A command-line tool to convert images from WebP format to other formats. "
            f"Supported output formats: {', '.join(VALID_OUTPUT_FORMATS)}. "
            "Animated WebP files are converted using their first frame only."
        ),
        epilog=(
            "Examples:\n"
            "  python webp_converter.py input.webp --output output.png\n"
            "  python webp_converter.py input.webp -o output.jpg --quality 80\n"
            "  python webp_converter.py input.webp -o output.png --overwrite"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "input_file",
        type=Path,
        help="Path to the input WebP file.",
    )

    parser.add_argument(
        "-o",
        "--output",
        dest="output_file",
        type=Path,
        required=True,
        help="Output path, including the desired format extension.",
    )

    # optional arguments
    parser.add_argument(
        "-q",
        "--quality",
        type=int,
        default=DEFAULT_JPEG_QUALITY,
        choices=range(MIN_JPEG_QUALITY, MAX_JPEG_QUALITY + 1),
        metavar=f"{MIN_JPEG_QUALITY}-{MAX_JPEG_QUALITY}",
        help=f"JPEG quality (default: {DEFAULT_JPEG_QUALITY}). Ignored for other formats.",
    )

    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace the output file if it already exists.",
    )

    return parser


def validate_input_file(input_file: Path) -> None:
    """
    Validate the input file path and extension.

    Parameters
    ----------
    input_file : Path
        Path to the input WebP file.

    Raises
    ------
    FileNotFoundError
        If the input path is not an existing file.
    ValueError
        If the input file does not have a .webp extension.
    """
    if not input_file.is_file():
        raise FileNotFoundError(
            "Invalid input file path: input file does not exist or is not a file. "
            f"Got {input_file}"
        )

    if input_file.suffix.lower() != ".webp":
        raise ValueError(
            "Invalid input file format: input file must be a WebP file. "
            f"Got {input_file.suffix}"
        )


def validate_output_file(output_file: Path, overwrite: bool) -> None:
    """
    Validate the output file path and format.

    Parameters
    ----------
    output_file : Path
        Path to the output file (with desired format extension).
    overwrite : bool
        Whether an existing output file may be replaced.

    Raises
    ------
    ValueError
        If the output file format is not supported or the path is a directory.
    FileExistsError
        If the output file exists and overwriting is not enabled.
    """
    if output_file.suffix.lower() not in VALID_OUTPUT_FORMATS:
        raise ValueError(
            "Invalid output file format: output file must be one of the following formats: "
            f"{', '.join(VALID_OUTPUT_FORMATS)}. Got {output_file.suffix}"
        )

    if output_file.is_dir():
        raise ValueError(f"Invalid output file path: path is a directory. Got {output_file}")

    if output_file.exists() and not overwrite:
        raise FileExistsError(
            f"Output file already exists: {output_file}. Use --overwrite to replace it."
        )


def flatten_to_rgb(img: Image.Image) -> Image.Image:
    """
    Convert an image to RGB, compositing any transparency onto a white background.

    Parameters
    ----------
    img : Image.Image
        The source image in any mode.

    Returns
    -------
    Image.Image
        An RGB image with no alpha channel.
    """
    if img.mode == "RGB":
        return img

    rgba = img.convert("RGBA")
    background = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
    return Image.alpha_composite(background, rgba).convert("RGB")


def convert_webp_image(
    input_file: Path,
    output_file: Path,
    quality: int = DEFAULT_JPEG_QUALITY,
) -> None:
    """
    Convert a WebP image to another format.

    This function:
    1. Opens the input file and confirms that it is a WebP image.
    2. Warns on stderr if the image is animated, as only the first frame is kept.
    3. Flattens transparency onto white when the output is JPEG.
    4. Writes the image to the output file, preserving any ICC colour profile.

    Parameters
    ----------
    input_file : Path
        Path to the input WebP file.
    output_file : Path
        Path to the output file (with desired format extension).
    quality : int
        JPEG quality, used only for JPEG output.

    Raises
    ------
    ValueError
        If the file content is not WebP data.
    OSError
        If the image cannot be read or written. This includes
        PIL.UnidentifiedImageError for unreadable files.
    """
    suffix = output_file.suffix.lower()

    with Image.open(input_file) as img:
        if img.format != "WEBP":
            raise ValueError(
                "Invalid input file content: file is not a WebP image. "
                f"Detected format: {img.format}"
            )

        if getattr(img, "is_animated", False):
            print(
                f"Warning: {input_file} is animated. Only the first frame will be converted.",
                file=sys.stderr,
            )

        save_kwargs: dict[str, object] = {}

        icc_profile = img.info.get("icc_profile")
        if icc_profile and suffix != ".bmp":
            save_kwargs["icc_profile"] = icc_profile

        if suffix in JPEG_EXTENSIONS:
            save_kwargs["quality"] = quality
            output_img = flatten_to_rgb(img)
        else:
            output_img = img

        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_img.save(output_file, **save_kwargs)


def main(argv: list[str] | None = None) -> int:
    """
    Parse command line arguments and run the conversion.

    Parameters
    ----------
    argv : list[str] | None
        Arguments to parse. Defaults to sys.argv[1:] when None.

    Returns
    -------
    int
        Exit code: 0 on success, 1 on failure.
    """
    args: argparse.Namespace = build_arg_parser().parse_args(argv)

    try:
        validate_input_file(args.input_file)
        validate_output_file(args.output_file, args.overwrite)
        convert_webp_image(args.input_file, args.output_file, args.quality)
    except (ValueError, OSError) as exception:
        print(
            f"Could not convert {args.input_file} to {args.output_file}. "
            f"Error: {exception}",
            file=sys.stderr,
        )
        return 1

    print(f"Converted {args.input_file} to {args.output_file}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())