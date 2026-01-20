# Photo Mixer - Justfile for common tasks

# Variables
venv_name := "venv"
venv_pip := "./{{venv_name}}/bin/pip"
venv_python := "./{{venv_name}}/bin/python"


# Default recipe - show available commands
default:
    @just --list --unsorted

# Create virtual environment
setup-venv:
    @printf "\033[36mCreating virtual environment...\033[0m\n"
    python3 -m venv {{venv_name}}
    @printf "\033[32m✓ Virtual environment created in ./{{venv_name}}\033[0m\n"
    @echo ""
    @printf "\033[33mActivate the virtual environment with:\033[0m\n"
    @printf "\033[1m\033[36m    source {{venv_name}}/bin/activate\033[0m\n"
    @echo ""
    @printf "\033[33mDeactivate the virtual environment with:\033[0m\n"
    @printf "\033[1m\033[36mdeactivate\033[0m\n"
    @echo ""

# Install dependencies/packages
install-packages:
    @printf "\033[36mInstalling dependencies/packages...\033[0m\n"
    ./{{venv_name}}/bin/pip install --upgrade pip
    ./{{venv_name}}/bin/pip install -r requirements.txt
    @printf "\033[32m✓ Dependencies/packages installed\033[0m\n"
    @echo ""


# Clean virtual environment
clean:
    @printf "\033[33mRemoving virtual environment...\033[0m\n"
    rm -rf {{venv_name}}
    @printf "\033[32m✓ Virtual environment removed\033[0m\n"
    @echo ""

# Install Sleepless dependencies
install-sleepless:
    @printf "\033[36mInstalling Sleepless dependencies...\033[0m\n"
    ./{{venv_name}}/bin/pip install --upgrade pip
    ./{{venv_name}}/bin/pip install -r sleepless/requirements.txt
    @printf "\033[32m✓ Sleepless dependencies installed\033[0m\n"
    @echo ""

# Run Sleepless menubar app
run-sleepless:
    @printf "\033[36mStarting Sleepless menubar app...\033[0m\n"
    ./{{venv_name}}/bin/python sleepless/menubar_sleepless.py

# Build Sleepless app bundle
build-sleepless:
    @printf "\033[36mBuilding Sleepless.app...\033[0m\n"
    cd sleepless && ./build.sh
    @printf "\033[32m✓ Build complete! Check sleepless/Sleepless.app\033[0m\n"

# Build Sleepless app with PyInstaller (requires: pip install pyinstaller)
build-sleepless-pyinstaller:
    @printf "\033[36mBuilding Sleepless.app with PyInstaller...\033[0m\n"
    ./{{venv_name}}/bin/pyinstaller sleepless/sleepless.spec
    @printf "\033[32m✓ Build complete! Check dist/Sleepless.app\033[0m\n"

# Show help
help:
    @printf "\033[1m\033[34mAvailable commands:\033[0m\n"
    @echo ""
    @printf "\033[36m  just setup-venv\033[0m           - Create venv\n"
    @printf "\033[36m  just install-packages\033[0m     - Install dependencies/packages\n"
    @printf "\033[36m  just install-sleepless\033[0m     - Install Sleepless dependencies\n"
    @printf "\033[36m  just run-sleepless\033[0m         - Run Sleepless menubar app\n"
    @printf "\033[36m  just build-sleepless\033[0m       - Build Sleepless.app bundle\n"
    @printf "\033[36m  just clean\033[0m                - Remove virtual environment\n"
    @printf "\033[36m  just help\033[0m                 - Show this help\n"
    @echo ""


