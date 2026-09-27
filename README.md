# AI Background Remover

Local Windows/Python background removal using BRIA RMBG-2.0. It creates a white-background PNG while preserving the original image dimensions.

## Requirements

- Windows and Python 3.11 (recommended; tested with model inference)
- `pyproject.toml` permits Python 3.10 and newer, but Python 3.10 has not yet been tested
- PyTorch (CPU works; CUDA is selected automatically when available)
- Access to and a Hugging Face login for the gated [`briaai/RMBG-2.0`](https://huggingface.co/briaai/RMBG-2.0) model

## Installation

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\hf.exe auth login
```

Open the model page above and accept BRIA's licence before the first run. The first invocation downloads model files to `models/RMBG-2.0/`; later runs load directly from that project folder. Keep this folder when transferring the application to another PC.

## Licensing

The original project code is licensed under MIT; see [LICENSE](LICENSE). This does not cover BRIA RMBG-2.0 model weights or other third-party components. BRIA's model weights are licensed under [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/) for non-commercial use; commercial use requires a separate agreement with BRIA. Dependencies retain their respective licenses.

## Browser app

Install the added Flask dependency, then start the local web app:
```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe scripts\run_web.py
```

The server loads RMBG-2.0 before it begins listening, so startup may take a while; after startup, the model is already in memory for image submissions. Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser. Upload an image and select **Process image** to compare the original and result side by side. Select **Save processed image** to choose a destination and filename. Edge and Chrome use a save-location picker; other browsers use their normal download behavior. Uploads are temporary and are not added to `input`.

## Command-line use

```powershell
.\.venv\Scripts\python.exe scripts\run_cli.py --input input\person.jpg
.\.venv\Scripts\python.exe scripts\run_cli.py --input input\person.jpg --output output\person_no_bg.png
.\.venv\Scripts\python.exe scripts\run_cli.py --input-dir input --output-dir output
.\.venv\Scripts\python.exe scripts\run_cli.py --input input\person.jpg --width 600 --height 600 --document-type photo
.\.venv\Scripts\python.exe scripts\run_cli.py --input input\signature.png --width 400 --height 150 --document-type signature --resize-mode crop --image-format jpeg --max-kb 100
```

The default output is a full-size PNG with a clean white background, using RMBG-2.0's soft alpha mask. Use `--background transparent` when you need an RGBA cutout instead. Review BRIA RMBG-2.0's licence before commercial use.

For upload-ready files, provide `--width` and `--height`. Photos use fit-with-white-padding by default; signatures, thumb impressions, and declarations use crop-to-fit by default. Select `--resize-mode fit` for white padding or `--resize-mode crop` for any document type. Add `--sharpen` for gentle post-resize sharpening. PNG is lossless; JPEG is smaller in many cases but lossy, and the CLI reports that warning. `--min-kb` makes the exporter try less compression or higher JPEG quality to reach the requested minimum without changing dimensions; it warns if that cannot be achieved within `--max-kb`.

## Running tests

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

GitHub Actions runs the same suite on Python 3.10 and 3.11. Tests use a fake processor, so they do not download model weights or require Hugging Face authentication.

## Layout

```text
src/image_editor/models/          RMBG-2.0 adapter
src/image_editor/processing/      validation, resizing, and export
src/image_editor/services/        shared processing pipeline
src/image_editor/interfaces/      CLI and Flask adapters
scripts/run_cli.py                CLI launcher
scripts/run_web.py                browser-app launcher
web/                              templates and static browser assets
models/                           downloaded model and transformer cache
input/                            source images
output/                           generated files
```
