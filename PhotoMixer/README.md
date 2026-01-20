# Photo Mixer

A Python tool to combine/mix two photos - a background image and a foreground image.

## Installation

### Option 1: Using Just (Recommended)

If you have [just](https://github.com/casey/just) installed:

```bash
just setup
```

This will create a virtual environment and install all dependencies.

### Option 2: Manual Installation

1. Create a virtual environment (optional but recommended):
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Using Just

If you set up with `just setup`, you can run:

**Basic usage:**
```bash
just run images/original/bg.jpg images/original/fg.jpg
```

**With all options:**
```bash
just run bg.jpg fg.jpg output=result.jpg blend_mode=multiply opacity=0.9
```

**With partial options:**
```bash
just run bg.jpg fg.jpg blend_mode=overlay
just run bg.jpg fg.jpg opacity=0.5
```

> **Note:** When using Just, use `blend_mode` (underscore) for the parameter name, even though the Python script accepts `--blend-mode` (hyphen).

**Available Just commands:**
- `just setup` - Create venv and install dependencies
- `just install` - Install dependencies (creates venv if needed)
- `just run <bg> <fg> [options]` - Run photo mixer
- `just clean` - Remove virtual environment
- `just help` - Show help message

See all available commands:
```bash
just help
```

### Direct Python Usage

Run the photo mixer script with command-line arguments:

```bash
python src/photo_mixer.py --background <bg-image> --foreground <fg-image>
```

### Required Arguments

- `--background` or `-b`: Path to the background image (base/larger image that stays full size)
- `--foreground` or `-f`: Path to the foreground image (will be overlaid and resized on background)

### Optional Arguments

- `--output` or `-o`: Output path for the mixed image (default: `images/mixed/mixed_<bg>_<fg>.jpg`)
- `--blend-mode` or `-m`: Blending mode - `normal` (default), `multiply`, `screen`, or `overlay`
- `--opacity` or `-p`: Foreground opacity from 0.0 to 1.0 (default: 0.8)

## Features

- **Command-line interface** - Easy to use with command-line arguments
- **Automatic resizing** - Foreground image is automatically resized to fit nicely on the background
- **Multiple blend modes** - Choose from Normal, Multiply, Screen, or Overlay blending
- **Opacity control** - Adjust how transparent the foreground image appears
- **Auto-saves** - Mixed images are automatically saved with descriptive names

## Examples

### Using Just

**Basic usage:**
```bash
just run images/original/pexels-shukran-1534411.jpg images/original/dubai-vae-02-june-2024-600nw-2476875599.webp
```

**With custom blend mode and opacity:**
```bash
just run bg.jpg fg.jpg blend_mode=multiply opacity=0.9
```

**With custom output path:**
```bash
just run bg.jpg fg.jpg output=my_result.jpg
```

**With all options:**
```bash
just run bg.jpg fg.jpg output=result.jpg blend_mode=overlay opacity=0.7
```

### Using Python Directly

**Basic usage:**
```bash
python src/photo_mixer.py --background images/original/pexels-shukran-1534411.jpg --foreground images/original/dubai-vae-02-june-2024-600nw-2476875599.webp
```

**With custom blend mode and opacity:**
```bash
python src/photo_mixer.py --background bg.jpg --foreground fg.jpg --blend-mode multiply --opacity 0.9
```

**With custom output path:**
```bash
python src/photo_mixer.py --background bg.jpg --foreground fg.jpg --output my_result.jpg
```

**Short form:**
```bash
python src/photo_mixer.py -b bg.jpg -f fg.jpg -m overlay -p 0.7 -o result.jpg
```

## Help

To see all available options:
```bash
python src/photo_mixer.py --help
```

