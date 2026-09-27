"""Application-level image processing workflow."""

from __future__ import annotations

import threading
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory

from PIL import Image

from ..models.rmbg import BackgroundRemover
from ..processing.exporting import ExportResult, ExportSettings, ImageExporter
from ..processing.validation import validate_image


@dataclass(frozen=True)
class ProcessedImage:
    """Encoded output independent of the CLI or web transport."""

    data: bytes
    filename: str
    size_kb: float
    warnings: tuple[str, ...]


class ImageProcessor:
    """Coordinate validation, background removal, resizing, and export."""

    def __init__(self, remover: BackgroundRemover | None = None, exporter: ImageExporter | None = None) -> None:
        self._remover = remover
        self._exporter = exporter or ImageExporter()
        self._model_lock = threading.Lock()

    @property
    def remover(self) -> BackgroundRemover:
        if self._remover is None:
            with self._model_lock:
                if self._remover is None:
                    self._remover = BackgroundRemover()
        return self._remover

    def load_model(self) -> BackgroundRemover:
        """Load and return the shared model before processing begins."""
        return self.remover

    def process_to_path(
        self,
        input_path: str | Path,
        output_path: str | Path,
        settings: ExportSettings,
        background: str = "white",
    ) -> ExportResult:
        source = validate_image(input_path)
        result = self.remover.remove_background_image(source, background)
        return self._exporter.export(result, output_path, settings)

    def process_to_bytes(
        self,
        input_path: str | Path,
        settings: ExportSettings,
        background: str = "white",
    ) -> ProcessedImage:
        with TemporaryDirectory(prefix="image-editor-") as temporary_folder:
            output = self.process_to_path(input_path, Path(temporary_folder) / "upload-ready", settings, background)
            return ProcessedImage(output.path.read_bytes(), output.path.name, output.size_kb, output.warnings)
