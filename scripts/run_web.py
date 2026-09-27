"""Local browser-app launcher."""

from __future__ import annotations

import logging
import sys

from image_editor.exceptions import ModelLoadError
from image_editor.interfaces.web import create_app
from image_editor.services.pipeline import ImageProcessor

LOGGER = logging.getLogger(__name__)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    processor = ImageProcessor()
    try:
        LOGGER.info("Loading RMBG-2.0 before starting the web server...")
        remover = processor.load_model()
    except ModelLoadError as exc:
        LOGGER.error("Unable to start the web app: %s", exc)
        return 1

    LOGGER.info("Model ready on %s (loaded in %.2f seconds).", remover.device_label, remover.model_load_seconds)
    app = create_app(processor)
    app.run(host="127.0.0.1", port=5000, debug=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
