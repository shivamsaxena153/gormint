# To Do

## 2026-09-20 — Image sizing and export

- [x] Add a resize/export module that preserves the original image and writes a separate upload-ready file.
- [x] For passport photos, use **fit within the target dimensions with white padding**. Do not stretch or crop the face.
- [x] For signatures, thumb impressions, and handwritten declarations, provide **crop-to-fit** and **fit-with-white-padding** modes.
- [x] Use high-quality Lanczos downscaling.
- [x] Add optional gentle sharpening after resizing only.
- [x] Support editable width, height, minimum KB, and maximum KB requirements.
- [x] Support lossless PNG and JPEG compatibility output, clearly warning that JPEG compression is lossy.

## 2026-09-26 - Package restructuring

- [x] Separate model, processing, service, and interface layers.
- [x] Add installable `src/image_editor` package with CLI and web adapters.
- [x] Move browser templates and static assets under `web/`.
