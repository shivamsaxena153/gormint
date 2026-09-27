"""Application paths and model configuration."""

from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODEL_ID = "briaai/RMBG-2.0"
MODEL_INPUT_SIZE = (1024, 1024)
MODEL_DIRECTORY = Path(os.environ.get("IMAGE_EDITOR_MODEL_DIRECTORY", PROJECT_ROOT / "models" / "RMBG-2.0"))
MODULE_CACHE_DIRECTORY = Path(os.environ.get("IMAGE_EDITOR_MODULE_CACHE", PROJECT_ROOT / "models" / "transformers_modules"))
SUPPORTED_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}
