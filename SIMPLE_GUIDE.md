# AI Background Remover — Simple Guide

## What this project does

This tool removes the background from a picture on your own computer.

For example, if you have a photo of a person standing in a room, the tool keeps the person, removes the room behind them, and places them on a plain white background.

It can be useful before making a passport-style image, product image, profile picture, signature image, or other clean image.

## Your privacy

Your actual photos are processed on your computer. They are not sent to a background-removal website or cloud API.

The first setup downloaded the AI model from Hugging Face. After that, the model is stored in this project and can run without internet access.

## Where to put your photo

Open this folder:

```text
gormintExamImageEditor\input
```

Copy your image into it. For example:

```text
gormintExamImageEditor\input\person.jpg
```

The tool accepts common formats such as JPG, JPEG, PNG, WEBP, BMP, and TIFF.

## How to remove one background

Open PowerShell in the project folder and run this command:

```powershell
.\.venv\Scripts\python.exe scripts\run_cli.py --input input\person.jpg
```

Change `person.jpg` to the real filename of your image.

## Where the finished image is saved

The result appears in this folder:

```text
gormintExamImageEditor\output
```

For the example above, the output will be:

```text
output\person_no_bg.png
```

The output is a PNG file with a white background. It keeps the same width and height as the original image.

## Keep a transparent background instead

White is the default. If you want a cutout with no background, use:

```powershell
.\.venv\Scripts\python.exe scripts\run_cli.py --input input\person.jpg --background transparent
```

## Choose a different output name

Use this command when you want to choose the output filename yourself:

```powershell
.\.venv\Scripts\python.exe scripts\run_cli.py --input input\person.jpg --output output\clean-person.png
```

## Process every image in the input folder

Put several images in `input`, then run:

```powershell
.\.venv\Scripts\python.exe scripts\run_cli.py --input-dir input --output-dir output
```

The model loads once, then processes every supported image in that folder.

## Why the web app takes time to start

The AI model is large, about 885 MB. The web app loads it into memory before it starts listening, so the first startup can take a while. After that, the model is ready when you submit an image. On this computer it uses the CPU because no NVIDIA GPU was detected, so the image processing itself can still take some time.

This is normal. A PC with a compatible NVIDIA GPU will be detected automatically and can run the model faster.

## Moving the project to another computer

Copy the complete `gormintExamImageEditor` folder, including the `models` folder. Do **not** copy the `.venv` folder.

On the new computer, install Python 3.11, then open PowerShell in the project folder and run:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install -e .
```

The copied `models` folder contains the downloaded RMBG-2.0 model, so it does not need to download again.

## If something goes wrong

- **“Input image not found”**: Check the filename and make sure the image is inside `input`.
- **The background is not transparent**: This is expected because white is the default. Use `--background transparent` when you need a transparent PNG.
- **The result removes part of the subject**: Try a clearer, higher-resolution original image with good lighting and stronger contrast between the subject and the background.
- **It is slow**: This is expected on CPU. Keep the program open until it finishes.

## Important note about licensing

This project uses BRIA RMBG-2.0. Read and follow its licence terms before using it commercially.
