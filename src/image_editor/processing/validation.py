"""Image validation and path helpers."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError

from ..config import SUPPORTED_SUFFIXES
from ..exceptions import ImageValidationError


def validate_image(path: str | Path) -> Path:
    """Return a resolved image path after checking it can be opened by Pillow."""
    image_path = Path(path).expanduser().resolve()
    if not image_path.is_file():
        raise ImageValidationError(f"Input image not found: {image_path}")
    if image_path.suffix.lower() not in SUPPORTED_SUFFIXES:
        raise ImageValidationError(f"Unsupported image format: {image_path.suffix or '(no extension)'}")
    try:
        with Image.open(image_path) as image:
            image.verify()
    except (UnidentifiedImageError, OSError) as exc:
        raise ImageValidationError(f"The supplied file is not a valid image: {image_path}") from exc
    return image_path


def load_display_oriented_rgb(path: str | Path) -> Image.Image:
    """Load an image with its EXIF display orientation applied."""
    with Image.open(path) as opened:
        return ImageOps.exif_transpose(opened).convert("RGB")


def create_output_path(input_path: str | Path, output_path: str | Path | None = None) -> Path:
    source = Path(input_path)
    destination = Path(output_path) if output_path else Path("output") / f"{source.stem}_no_bg.png"
    destination = destination.expanduser()
    if destination.suffix.lower() != ".png":
        destination = destination.with_suffix(".png")
    destination.parent.mkdir(parents=True, exist_ok=True)
    return destination.resolve()


def iter_images(directory: str | Path) -> list[Path]:
    folder = Path(directory).expanduser().resolve()
    if not folder.is_dir():
        raise ImageValidationError(f"Input directory not found: {folder}")
    return sorted(item for item in folder.iterdir() if item.is_file() and item.suffix.lower() in SUPPORTED_SUFFIXES)
