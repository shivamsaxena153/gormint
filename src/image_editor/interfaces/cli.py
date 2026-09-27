"""Command-line adapter for the image processing service."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from ..exceptions import ExportError, ImageValidationError, ModelLoadError
from ..processing.exporting import ExportSettings
from ..processing.validation import iter_images, validate_image
from ..services.pipeline import ImageProcessor


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Remove image backgrounds locally with BRIA RMBG-2.0.")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--input", type=Path, help="One input image.")
    source.add_argument("--input-dir", type=Path, help="Directory of input images.")
    parser.add_argument("--output", type=Path, help="Output file for --input.")
    parser.add_argument("--output-dir", type=Path, default=Path("output"), help="Directory for batch outputs.")
    parser.add_argument("--background", choices=("white", "transparent"), default="white")
    parser.add_argument("--width", type=int)
    parser.add_argument("--height", type=int)
    parser.add_argument("--document-type", choices=("photo", "signature", "thumb", "declaration"), default="photo")
    parser.add_argument("--resize-mode", choices=("auto", "fit", "crop"), default="auto")
    parser.add_argument("--image-format", choices=("png", "jpeg"), default="png")
    parser.add_argument("--min-kb", type=int)
    parser.add_argument("--max-kb", type=int)
    parser.add_argument("--sharpen", action="store_true")
    parser.add_argument("--debug", action="store_true")
    return parser.parse_args()


def build_settings(args: argparse.Namespace) -> ExportSettings:
    settings = ExportSettings(
        width=args.width,
        height=args.height,
        document_type=args.document_type,
        resize_mode=args.resize_mode,
        image_format=args.image_format,
        min_kb=args.min_kb,
        max_kb=args.max_kb,
        sharpen=args.sharpen,
    )
    settings.validate()
    return settings


def run() -> int:
    args = parse_args()
    configure_logging(args.debug)
    logger = logging.getLogger(__name__)
    try:
        if args.output and not args.input:
            raise ExportError("--output can only be used with --input.")
        settings = build_settings(args)
        processor = ImageProcessor()
        if args.input:
            source = validate_image(args.input)
            destination = args.output or Path("output") / f"{source.stem}_no_bg"
            export = processor.process_to_path(source, destination, settings, args.background)
            print(f"Output : {export.path}")
            for warning in export.warnings:
                logger.warning("WARNING: %s", warning)
            return 0

        inputs = iter_images(args.input_dir)
        if not inputs:
            raise ImageValidationError(f"No supported images found in {args.input_dir}")
        args.output_dir.mkdir(parents=True, exist_ok=True)
        for image_path in inputs:
            try:
                export = processor.process_to_path(
                    image_path, args.output_dir / f"{image_path.stem}_no_bg", settings, args.background
                )
                print(f"Output : {export.path}")
                for warning in export.warnings:
                    logger.warning("WARNING: %s: %s", image_path.name, warning)
            except (ImageValidationError, OSError, RuntimeError) as exc:
                logger.error("ERROR: %s", exc)
                if args.debug:
                    logger.exception("Detailed processing error")
                return 1
        return 0
    except (ExportError, ImageValidationError, ModelLoadError, OSError, RuntimeError) as exc:
        logger.error("ERROR: %s", exc)
        if args.debug:
            logger.exception("Detailed error")
        return 1


def configure_logging(debug: bool) -> None:
    logging.basicConfig(level=logging.DEBUG if debug else logging.INFO, format="%(message)s")


if __name__ == "__main__":
    sys.exit(run())
