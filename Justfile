# PySuite — monorepo Justfile (run from repository root)

# Variables
venv_name := "venv"
venv_pip := "./" + venv_name + "/bin/pip"
venv_python := "./" + venv_name + "/bin/python"


# Default recipe — show available commands
default:
    @just --list --unsorted

# ── Shared root venv (optional; PyCore & PhotoMixer also have their own) ──────

# Create virtual environment at repo root
setup-venv:
    @printf "\033[36mCreating virtual environment at repo root...\033[0m\n"
    python3 -m venv {{venv_name}}
    @printf "\033[32m✓ Virtual environment created in ./{{venv_name}}\033[0m\n"
    @echo ""
    @printf "\033[33mActivate with:\033[0m source {{venv_name}}/bin/activate\n"

# Install root requirements.txt (PyCore deps mirrored at root)
install-packages:
    @printf "\033[36mInstalling root dependencies...\033[0m\n"
    {{venv_pip}} install --upgrade pip
    {{venv_pip}} install -r requirements.txt
    @printf "\033[32m✓ Dependencies installed from requirements.txt\033[0m\n"

# Remove root virtual environment
clean:
    @printf "\033[33mRemoving root virtual environment...\033[0m\n"
    rm -rf {{venv_name}}
    @printf "\033[32m✓ Virtual environment removed\033[0m\n"

# ── PyCore (document converter, time utils, office, exceptions) ───────────────

# Run any PyCore Justfile recipe — e.g. `just pycore list`
pycore *ARGS:
    just --justfile PyCore/Justfile {{ARGS}}

# ── PhotoMixer (image blending) ───────────────────────────────────────────────

# Run any PhotoMixer Justfile recipe — e.g. `just photomixer run bg.jpg fg.jpg`
photomixer *ARGS:
    just --justfile PhotoMixer/Justfile {{ARGS}}

# ── PyCademy (learning scripts) ───────────────────────────────────────────────

# Run any PyCademy Justfile recipe — e.g. `just pycademy acronym`
pycademy *ARGS:
    just --justfile PyCademy/Justfile {{ARGS}}

# ── PyTools (migration index) ─────────────────────────────────────────────────

# Run any PyTools Justfile recipe — e.g. `just pytools index`
pytools *ARGS:
    just --justfile PyTools/Justfile {{ARGS}}

# ── PyPatterns (design pattern examples) ──────────────────────────────────────

# Run any PyPatterns Justfile recipe — e.g. `just pypatterns singleton`
pypatterns *ARGS:
    just --justfile PyPatterns/Justfile {{ARGS}}

# ── Awake (macOS menubar sleep prevention) ────────────────────────────────────

# Install Awake dependencies into root venv
install-awake:
    @printf "\033[36mInstalling Awake dependencies...\033[0m\n"
    {{venv_pip}} install --upgrade pip
    {{venv_pip}} install -r Awake/requirements.txt
    @printf "\033[32m✓ Awake dependencies installed\033[0m\n"

# Run Awake menubar app
run-awake:
    @printf "\033[36mStarting Awake menubar app...\033[0m\n"
    {{venv_python}} Awake/menubar.py

# Build Awake.app bundle
build-awake:
    @printf "\033[36mBuilding Awake.app...\033[0m\n"
    cd Awake && ./build.sh
    @printf "\033[32m✓ Build complete! Check Awake/Awake.app\033[0m\n"

# Build Awake.app with PyInstaller (requires: pip install pyinstaller)
build-awake-pyinstaller:
    @printf "\033[36mBuilding Awake.app with PyInstaller...\033[0m\n"
    {{venv_python}} -m PyInstaller Awake/awake.spec
    @printf "\033[32m✓ Build complete! Check dist/Awake.app\033[0m\n"

# Show help
help:
    @printf "\033[1m\033[34mPySuite commands (run from repo root):\033[0m\n"
    @echo ""
    @printf "\033[33mShared venv:\033[0m\n"
    @printf "\033[36m  just setup-venv\033[0m              - Create root venv/\n"
    @printf "\033[36m  just install-packages\033[0m        - Install root requirements.txt\n"
    @printf "\033[36m  just clean\033[0m                   - Remove root venv/\n"
    @echo ""
    @printf "\033[33mPyCore\033[0m (or \033[36mcd PyCore\033[0m and use its Justfile):\n"
    @printf "\033[36m  just pycore setup-venv\033[0m        - PyCore-local venv\n"
    @printf "\033[36m  just pycore list\033[0m              - Document conversion formats\n"
    @printf "\033[36m  just pycore convert -i FILE pdf\033[0m - Convert a document\n"
    @printf "\033[36m  just pycore office --help\033[0m    - Office/Excel CLI\n"
    @printf "\033[36m  just pycore time-demo\033[0m         - UTC/TAI demo\n"
    @echo ""
    @printf "\033[33mPhotoMixer\033[0m (or \033[36mcd PhotoMixer\033[0m):\n"
    @printf "\033[36m  just photomixer setup\033[0m         - PhotoMixer venv + deps\n"
    @printf "\033[36m  just photomixer run BG FG\033[0m     - Blend two images\n"
    @echo ""
    @printf "\033[33mPyPatterns\033[0m (or \033[36mcd PyPatterns\033[0m):\n"
    @printf "\033[36m  just pypatterns singleton\033[0m     - Run Singleton demo\n"
    @printf "\033[36m  just pypatterns list\033[0m          - List patterns\n"
    @echo ""
    @printf "\033[33mAwake\033[0m (macOS menubar app):\n"
    @printf "\033[36m  just install-awake\033[0m           - Awake deps into root venv\n"
    @printf "\033[36m  just run-awake\033[0m               - Run menubar app\n"
    @printf "\033[36m  just build-awake\033[0m             - Build Awake.app\n"
    @echo ""
    @printf "\033[33mPyCademy\033[0m (or \033[36mcd PyCademy\033[0m):\n"
    @printf "\033[36m  just pycademy install-packages\033[0m  - Editable install\n"
    @printf "\033[36m  just pycademy acronym\033[0m            - Run acronym demo\n"
    @echo ""
    @printf "\033[33mPyTools\033[0m (migration index):\n"
    @printf "\033[36m  just pytools index\033[0m              - Print legacy path map\n"
    @echo ""
