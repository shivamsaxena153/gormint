"""Flask adapter for the local browser application."""

from __future__ import annotations

import threading
from io import BytesIO
import os
from pathlib import Path
import secrets
from tempfile import TemporaryDirectory

from flask import Flask, flash, jsonify, redirect, render_template, request, send_file, url_for
from werkzeug.datastructures import FileStorage

from ..exceptions import ExportError, ImageValidationError
from ..processing.exporting import ExportSettings
from ..processing.validation import validate_image
from ..services.pipeline import ImageProcessor

WEB_ROOT = Path(__file__).resolve().parents[3] / "web"


def create_app(processor: ImageProcessor | None = None) -> Flask:
    app = Flask(__name__, template_folder=str(WEB_ROOT / "templates"), static_folder=str(WEB_ROOT / "static"))
    app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024
    app.secret_key = os.environ.get("FLASK_SECRET_KEY") or secrets.token_hex(32)
    image_processor = processor or ImageProcessor()
    processing_lock = threading.Lock()

    def read_int(value: str | None) -> int | None:
        if not value or not value.strip():
            return None
        return int(value)

    def build_settings() -> ExportSettings:
        settings = ExportSettings(
            width=read_int(request.form.get("width")),
            height=read_int(request.form.get("height")),
            document_type=request.form.get("document_type", "photo"),
            resize_mode=request.form.get("resize_mode", "auto"),
            image_format=request.form.get("image_format", "png"),
            min_kb=read_int(request.form.get("min_kb")),
            max_kb=read_int(request.form.get("max_kb")),
            sharpen=request.form.get("sharpen") == "on",
        )
        settings.validate()
        return settings

    def save_upload(upload: FileStorage, directory: Path) -> Path:
        suffix = Path(upload.filename or "upload.png").suffix.lower() or ".png"
        candidate = directory / f"source{suffix}"
        upload.save(candidate)
        return validate_image(candidate)

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.post("/process")
    def process():
        upload = request.files.get("image")
        if upload is None or not upload.filename:
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return jsonify(error="Choose an image before processing."), 400
            flash("Choose an image before processing.", "error")
            return redirect(url_for("index"))
        try:
            settings = build_settings()
            with processing_lock:
                with TemporaryDirectory(prefix="image-editor-") as folder:
                    source = save_upload(upload, Path(folder))
                    processed = image_processor.process_to_bytes(source, settings, request.form.get("background", "white"))
            response = send_file(
                BytesIO(processed.data),
                as_attachment=False,
                download_name=processed.filename,
                mimetype="image/jpeg" if settings.image_format == "jpeg" else "image/png",
            )
            response.headers["X-Export-Size-KB"] = f"{processed.size_kb:.1f}"
            response.headers["X-Export-Filename"] = processed.filename
            if processed.warnings:
                response.headers["X-Export-Warnings"] = " | ".join(processed.warnings)
            return response
        except (ValueError, ImageValidationError, ExportError, OSError, RuntimeError) as exc:
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return jsonify(error=str(exc)), 400
            flash(str(exc), "error")
            return redirect(url_for("index"))

    @app.errorhandler(413)
    def request_too_large(_error):
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify(error="That image is larger than the 25 MB upload limit."), 413
        flash("That image is larger than the 25 MB upload limit.", "error")
        return redirect(url_for("index"))

    return app
