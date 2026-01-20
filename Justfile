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

# Install Awake dependencies
install-awake:
    @printf "\033[36mInstalling Awake dependencies...\033[0m\n"
    ./{{venv_name}}/bin/pip install --upgrade pip
    ./{{venv_name}}/bin/pip install -r awake/requirements.txt
    @printf "\033[32m✓ Awake dependencies installed\033[0m\n"
    @echo ""

# Run Awake menubar app
run-awake:
    @printf "\033[36mStarting Awake menubar app...\033[0m\n"
    ./{{venv_name}}/bin/python awake/menubar.py

# Build Awake app bundle
build-awake:
    @printf "\033[36mBuilding Awake.app...\033[0m\n"
    cd awake && ./build.sh
    @printf "\033[32m✓ Build complete! Check awake/Awake.app\033[0m\n"

# Build Awake app with PyInstaller (requires: pip install pyinstaller)
build-awake-pyinstaller:
    @printf "\033[36mBuilding Awake.app with PyInstaller...\033[0m\n"
    ./{{venv_name}}/bin/pyinstaller awake/awake.spec
    @printf "\033[32m✓ Build complete! Check dist/Awake.app\033[0m\n"

# Show help
help:
    @printf "\033[1m\033[34mAvailable commands:\033[0m\n"
    @echo ""
    @printf "\033[36m  just setup-venv\033[0m           - Create venv\n"
    @printf "\033[36m  just install-packages\033[0m     - Install dependencies/packages\n"
    @printf "\033[36m  just install-awake\033[0m        - Install Awake dependencies\n"
    @printf "\033[36m  just run-awake\033[0m            - Run Awake menubar app\n"
    @printf "\033[36m  just build-awake\033[0m          - Build Awake.app bundle\n"
    @printf "\033[36m  just clean\033[0m                - Remove virtual environment\n"
    @printf "\033[36m  just help\033[0m                 - Show this help\n"
    @echo ""
