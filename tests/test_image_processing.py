from __future__ import annotations

from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from PIL import Image

from image_editor.exceptions import ImageValidationError
from image_editor.interfaces.web import create_app
from image_editor.processing.exporting import ExportSettings, ImageExporter
from image_editor.processing.validation import load_display_oriented_rgb, validate_image
from image_editor.services.pipeline import ProcessedImage


class ImageProcessingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.exporter = ImageExporter()

    def test_load_applies_exif_display_orientation(self) -> None:
        with TemporaryDirectory() as folder:
            image_path = Path(folder) / "rotated.jpg"
            exif = Image.Exif()
            exif[274] = 6
            Image.new("RGB", (80, 40), "red").save(image_path, exif=exif)

            loaded = load_display_oriented_rgb(image_path)

        self.assertEqual(loaded.size, (40, 80))
        self.assertEqual(loaded.mode, "RGB")

    def test_validate_image_rejects_invalid_image(self) -> None:
        with TemporaryDirectory() as folder:
            invalid_path = Path(folder) / "invalid.png"
            invalid_path.write_text("not an image", encoding="utf-8")

            with self.assertRaises(ImageValidationError):
                validate_image(invalid_path)

    def test_fit_preserves_aspect_and_pads_canvas(self) -> None:
        source = Image.new("RGB", (40, 20), "red")
        settings = ExportSettings(width=40, height=40, document_type="photo")

        prepared, _ = self.exporter.prepare(source, settings)

        self.assertEqual(prepared.size, (40, 40))
        self.assertEqual(prepared.getpixel((20, 2)), (255, 255, 255))
        self.assertEqual(prepared.getpixel((20, 20)), (255, 0, 0))
        self.assertEqual(source.size, (40, 20))

    def test_crop_fills_requested_dimensions(self) -> None:
        source = Image.new("RGB", (40, 20), "blue")
        settings = ExportSettings(width=20, height=20, resize_mode="crop")

        prepared, _ = self.exporter.prepare(source, settings)

        self.assertEqual(prepared.size, (20, 20))
        self.assertEqual(prepared.getpixel((10, 10)), (0, 0, 255))

    def test_jpeg_respects_minimum_and_maximum_size(self) -> None:
        source = Image.new("RGB", (128, 128))
        source.putdata(
            [((index * 37) % 256, (index * 67) % 256, (index * 97) % 256) for index in range(128 * 128)]
        )
        settings = ExportSettings(image_format="jpeg", min_kb=2, max_kb=8)

        with TemporaryDirectory() as folder:
            result = self.exporter.export(source, Path(folder) / "result", settings)
            with Image.open(result.path) as exported:
                self.assertEqual(exported.format, "JPEG")
                self.assertEqual(exported.size, source.size)
            self.assertGreaterEqual(result.size_kb, 2)
            self.assertLessEqual(result.size_kb, 8)
            self.assertTrue(any("lossy" in warning.lower() for warning in result.warnings))

    def test_png_export_is_lossless(self) -> None:
        source = Image.new("RGB", (17, 13))
        source.putdata([((index * 13) % 256, (index * 29) % 256, (index * 43) % 256) for index in range(17 * 13)])

        with TemporaryDirectory() as folder:
            result = self.exporter.export(source, Path(folder) / "result", ExportSettings())
            with Image.open(result.path) as exported:
                self.assertEqual(exported.format, "PNG")
                self.assertEqual(exported.tobytes(), source.tobytes())

    def test_web_upload_returns_inline_image_and_metadata(self) -> None:
        class FakeProcessor:
            def process_to_bytes(self, input_path, settings, background):
                return ProcessedImage(b"test-image-data", "processed.png", 12.5, ())

        upload = BytesIO()
        Image.new("RGB", (10, 8), "white").save(upload, format="PNG")
        upload.seek(0)
        app = create_app(FakeProcessor())
        app.config["TESTING"] = True

        with app.test_client() as client:
            response = client.post(
                "/process",
                data={
                    "image": (upload, "source.png"),
                    "document_type": "photo",
                    "resize_mode": "auto",
                    "image_format": "png",
                    "background": "white",
                },
                headers={"X-Requested-With": "XMLHttpRequest"},
                content_type="multipart/form-data",
            )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.headers["Content-Disposition"].startswith("inline"))
        self.assertEqual(response.headers["X-Export-Filename"], "processed.png")
        self.assertEqual(response.data, b"test-image-data")


if __name__ == "__main__":
    unittest.main()
