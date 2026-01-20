# PySuite

A Python utility suite with time handling utilities and learning examples.

## Overview

PySuite is a collection of Python utilities and learning examples, featuring:
- **Time Utilities**: Advanced time handling with leap second support
- **Learning Examples**: Various Python code samples and exercises
- **Task Automation**: Justfile-based commands for common development tasks

## Prerequisites

- Python 3.12 or higher
- [Just](https://github.com/casey/just) (command runner)

### Installing Just

```bash
# macOS
brew install just

# Linux
curl --proto '=https' --tlsv1.2 -sSf https://just.systems/install.sh | bash -s -- --to ~/bin

# Windows
cargo install just
```

## Quick Start

### 1. Setup Virtual Environment

```bash
just setup-venv
```

This creates a virtual environment in the `venv` directory.

### 2. Activate Virtual Environment

```bash
source venv/bin/activate
```

### 3. Install Dependencies

```bash
just install-packages
```

This installs all required packages from `requirements.txt`.

## Available Commands

The project uses [Just](https://github.com/casey/just) for task automation. Run `just help` to see all available commands:

- `just setup-venv` - Create virtual environment
- `just install-packages` - Install dependencies/packages
- `just clean` - Remove virtual environment
- `just help` - Show help message

## Project Structure

```
PySuite/
├── core/                 # Core utilities
│   └── time/            # Time utilities with leap second support
│       └── time.py
├── learning/            # Learning examples and exercises
│   ├── acronym.py
│   ├── keyGenerator.py
│   ├── lists.py
│   ├── story.py
│   └── underscores.py
├── tests/               # Test files
├── main.py              # Main entry point
├── requirements.txt     # Python dependencies
├── Justfile            # Task automation commands
└── README.md           # This file
```

## Core Features

### Time Utilities

The `core.time.time` module provides utilities for handling time with leap second support:

```python
from core.time.time import TimeUtils
from datetime import datetime

# Get current UTC time
utc_time = TimeUtils.now()

# Get leap seconds
leap_seconds = TimeUtils.get_leap_seconds(utc_time)

# Convert UTC to TAI (International Atomic Time)
tai_time = TimeUtils.to_tai(utc_time)

# Convert TAI back to UTC
utc_time = TimeUtils.from_tai(tai_time)
```

#### Features:
- **Leap Second Handling**: Properly accounts for leap seconds added since 1972
- **TAI Conversion**: Convert between UTC and TAI (International Atomic Time)
- **Leap Second Data**: Uses the `leapseconddata` library for accurate leap second information

## Dependencies

- `leapseconddata` - Provides accurate leap second data

See `requirements.txt` for the complete list of dependencies.

## Development

### Running the Project

```bash
# Activate virtual environment
source venv/bin/activate

# Run main script
python main.py
```

### Cleaning Up

To remove the virtual environment:

```bash
just clean
```

## Notes

- The virtual environment is created in the `venv/` directory (gitignored)
- All commands use colorful output for better readability
- The project uses Python 3.12+ features

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]
