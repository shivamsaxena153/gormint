"""BRIA RMBG-2.0 model adapter."""

from __future__ import annotations

import logging
import os
import time
from pathlib import Path

from ..config import MODEL_DIRECTORY, MODEL_ID, MODEL_INPUT_SIZE, MODULE_CACHE_DIRECTORY
from ..exceptions import ModelLoadError

os.environ.setdefault("HF_MODULES_CACHE", str(MODULE_CACHE_DIRECTORY))

import torch
from huggingface_hub import snapshot_download
from PIL import Image
from torchvision import transforms
from transformers import AutoModelForImageSegmentation

LOGGER = logging.getLogger(__name__)


class BackgroundRemover:
    """Load RMBG-2.0 once and remove backgrounds from images."""

    def __init__(self) -> None:
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model_directory = MODEL_DIRECTORY
        self.transform = transforms.Compose(
            [
                transforms.Resize(MODEL_INPUT_SIZE),
                transforms.ToTensor(),
                transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
            ]
        )
        started = time.perf_counter()
        try:
            if not (self.model_directory / "config.json").is_file():
                snapshot_download(
                    repo_id=MODEL_ID,
                    local_dir=self.model_directory,
                    allow_patterns=["config.json", "*.py", "model.safetensors"],
                )
            self.model = AutoModelForImageSegmentation.from_pretrained(
                self.model_directory, trust_remote_code=True, local_files_only=True
            ).eval().to(self.device)
        except Exception as exc:
            raise ModelLoadError(
                "Unable to load RMBG-2.0. Confirm the model licence, login, and model files."
            ) from exc
        self.model_load_seconds = time.perf_counter() - started

    @property
    def device_label(self) -> str:
        if self.device.type == "cuda":
            return f"CUDA ({torch.cuda.get_device_name(0)})"
        return "CPU"

    def remove_background_image(self, image_path: str | Path, background: str = "white") -> Image.Image:
        """Return a full-resolution cutout image."""
        from ..processing.validation import load_display_oriented_rgb, validate_image

        source_path = validate_image(image_path)
        started = time.perf_counter()
        image = load_display_oriented_rgb(source_path)
        tensor = self.transform(image).unsqueeze(0).to(self.device)
        with torch.inference_mode():
            prediction = self.model(tensor)[-1].sigmoid().cpu()

        alpha = transforms.ToPILImage()(prediction[0].squeeze(0)).resize(image.size, Image.Resampling.LANCZOS)
        result = image.convert("RGBA")
        result.putalpha(alpha)
        if background == "white":
            white_canvas = Image.new("RGBA", image.size, "white")
            white_canvas.alpha_composite(result)
            result = white_canvas.convert("RGB")
        elif background != "transparent":
            raise ValueError(f"Unsupported background: {background}")
        LOGGER.info("Completed %s in %.2f seconds", source_path.name, time.perf_counter() - started)
        return result
