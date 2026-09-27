"""High-quality resizing and size-controlled export."""

from __future__ import annotations

from dataclasses import dataclass, field
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageFilter, ImageOps

from ..exceptions import ExportError


@dataclass(frozen=True)
class ExportSettings:
    width: int | None = None
    height: int | None = None
    document_type: str = "photo"
    resize_mode: str = "auto"
    image_format: str = "png"
    min_kb: int | None = None
    max_kb: int | None = None
    sharpen: bool = False

    def validate(self) -> None:
        if (self.width is None) != (self.height is None):
            raise ExportError("Width and height must be supplied together.")
        if self.width is not None and (self.width < 1 or self.height is None or self.height < 1):
            raise ExportError("Width and height must be positive whole numbers.")
        if self.document_type not in {"photo", "signature", "thumb", "declaration"}:
            raise ExportError("Document type must be photo, signature, thumb, or declaration.")
        if self.resize_mode not in {"auto", "fit", "crop"}:
            raise ExportError("Resize mode must be auto, fit, or crop.")
        if self.image_format not in {"png", "jpeg"}:
            raise ExportError("Image format must be png or jpeg.")
        if self.min_kb is not None and self.min_kb < 0:
            raise ExportError("Minimum KB cannot be negative.")
        if self.max_kb is not None and self.max_kb < 1:
            raise ExportError("Maximum KB must be at least 1.")
        if self.min_kb is not None and self.max_kb is not None and self.min_kb > self.max_kb:
            raise ExportError("Minimum KB cannot be greater than maximum KB.")

    @property
    def resolved_resize_mode(self) -> str:
        if self.resize_mode != "auto":
            return self.resize_mode
        return "fit" if self.document_type == "photo" else "crop"


@dataclass(frozen=True)
class ExportResult:
    path: Path
    size_kb: float
    warnings: tuple[str, ...] = field(default_factory=tuple)


class ImageExporter:
    """Resize and encode images without changing their source files."""

    def prepare(self, image: Image.Image, settings: ExportSettings) -> tuple[Image.Image, list[str]]:
        settings.validate()
        prepared = image.copy()
        warnings: list[str] = []
        if settings.width is None or settings.height is None:
            return prepared, warnings
        target = (settings.width, settings.height)
        source_width, source_height = prepared.size
        scale = max(target[0] / source_width, target[1] / source_height) if settings.resolved_resize_mode == "crop" else min(target[0] / source_width, target[1] / source_height)
        if scale > 1:
            warnings.append("The requested dimensions enlarge the source image, so it may appear softer.")
        if settings.resolved_resize_mode == "crop":
            prepared = ImageOps.fit(prepared, target, method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
        else:
            contained = ImageOps.contain(prepared, target, method=Image.Resampling.LANCZOS)
            has_alpha = "A" in contained.getbands()
            fill = (255, 255, 255, 0) if has_alpha else "white"
            canvas = Image.new(contained.mode, target, fill)
            position = ((target[0] - contained.width) // 2, (target[1] - contained.height) // 2)
            canvas.paste(contained, position, contained if has_alpha else None)
            prepared = canvas
        if settings.sharpen:
            prepared = prepared.filter(ImageFilter.UnsharpMask(radius=0.8, percent=90, threshold=3))
        return prepared, warnings

    def export(self, image: Image.Image, output_path: str | Path, settings: ExportSettings) -> ExportResult:
        prepared, warnings = self.prepare(image, settings)
        destination = Path(output_path).expanduser().resolve()
        destination.parent.mkdir(parents=True, exist_ok=True)
        extension = ".jpg" if settings.image_format == "jpeg" else ".png"
        if destination.suffix.lower() != extension:
            destination = destination.with_suffix(extension)
        if settings.image_format == "jpeg":
            warnings.append("JPEG output uses lossy compression; use PNG when lossless quality is required.")
        data = self._encode(prepared, settings)
        size_kb = len(data) / 1024
        if settings.max_kb is not None and size_kb > settings.max_kb:
            warning = "Lossless PNG exceeds the maximum size. Reduce dimensions or use JPEG if the exam permits it." if settings.image_format == "png" else "JPEG still exceeds the maximum size at its lowest usable quality."
            warnings.append(warning)
        if settings.min_kb is not None and size_kb < settings.min_kb:
            warnings.append("Could not reach the requested minimum size without changing dimensions or adding artificial data.")
        destination.write_bytes(data)
        return ExportResult(destination, size_kb, tuple(warnings))

    def _encode(self, image: Image.Image, settings: ExportSettings) -> bytes:
        if settings.image_format == "png":
            if settings.min_kb is None and settings.max_kb is None:
                return self._save(image, "PNG", optimize=True)
            limit = settings.max_kb * 1024 if settings.max_kb is not None else None
            minimum = settings.min_kb * 1024 if settings.min_kb is not None else None
            candidates = [
                self._save(image, "PNG", optimize=False, compress_level=level)
                for level in range(9, -1, -1)
            ]
            within_max = [data for data in candidates if limit is None or len(data) <= limit]
            if not within_max:
                return min(candidates, key=len)
            meeting_minimum = [data for data in within_max if minimum is not None and len(data) >= minimum]
            if meeting_minimum:
                return min(meeting_minimum, key=len)
            if minimum is not None:
                return max(within_max, key=len)
            return min(within_max, key=len)
        if "A" in image.getbands():
            white_background = Image.new("RGBA", image.size, "white")
            white_background.alpha_composite(image.convert("RGBA"))
            rgb = white_background.convert("RGB")
        else:
            rgb = image.convert("RGB")
        if settings.max_kb is None and settings.min_kb is None:
            return self._save(rgb, "JPEG", quality=92, subsampling=0, optimize=True)
        if settings.max_kb is None:
            minimum = settings.min_kb * 1024
            best = self._save(rgb, "JPEG", quality=100, subsampling=0, optimize=True)
            if len(best) < minimum:
                best = self._save(rgb, "JPEG", quality=100, subsampling=0, optimize=False)
            return best

        limit = settings.max_kb * 1024
        minimum = settings.min_kb * 1024 if settings.min_kb is not None else None
        candidates: list[tuple[int, bytes]] = []
        for optimize in (True, False):
            best: tuple[int, bytes] | None = None
            low, high = 35, 100
            while low <= high:
                quality = (low + high) // 2
                candidate = self._save(rgb, "JPEG", quality=quality, subsampling=0, optimize=optimize)
                if len(candidate) <= limit:
                    best = (quality, candidate)
                    low = quality + 1
                else:
                    high = quality - 1
            if best is not None:
                candidates.append(best)
        if not candidates:
            return self._save(rgb, "JPEG", quality=35, subsampling=0, optimize=True)
        if minimum is not None:
            meeting_minimum = [item for item in candidates if len(item[1]) >= minimum]
            if meeting_minimum:
                return max(meeting_minimum, key=lambda item: (item[0], -len(item[1])))[1]
        return max(candidates, key=lambda item: (item[0], -len(item[1])))[1]

    @staticmethod
    def _save(image: Image.Image, image_format: str, **options: object) -> bytes:
        buffer = BytesIO()
        image.save(buffer, image_format, **options)
        return buffer.getvalue()
