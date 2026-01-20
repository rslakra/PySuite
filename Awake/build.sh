#!/bin/bash
# Build script for creating a macOS .app bundle from the Awake menubar application

set -e

# Help function
show_help() {
    cat << EOF
Usage: ./build.sh [OPTIONS]

Build script for creating a macOS .app bundle from the Awake menubar application.

OPTIONS:
    -q, --quiet    Automatically bundle virtual environment without prompting
    -h, --help     Display this help message and exit

EXAMPLES:
    ./build.sh              Interactive mode (prompts for venv bundling)
    ./build.sh --quiet      Quiet mode (automatically bundles venv)
    ./build.sh -q           Same as --quiet
    ./build.sh --help       Show this help message

The script will:
  - Create the Awake.app bundle structure
  - Copy necessary files
  - Optionally create a bundled virtual environment
  - Set proper permissions

For more information, see README.md
EOF
    exit 0
}

# Parse command line arguments
QUIET=false
if [[ "$1" == "--help" ]] || [[ "$1" == "-h" ]]; then
    show_help
elif [[ "$1" == "--quiet" ]] || [[ "$1" == "-q" ]]; then
    QUIET=true
elif [[ -n "$1" ]]; then
    echo "Unknown option: $1" >&2
    echo "Use --help for usage information" >&2
    exit 1
fi

APP_NAME="Awake"
APP_BUNDLE="${APP_NAME}.app"
APP_DIR="${APP_BUNDLE}/Contents"
MACOS_DIR="${APP_DIR}/MacOS"
RESOURCES_DIR="${APP_DIR}/Resources"
SCRIPT_NAME="awake_launcher"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RESET='\033[0m'

echo -e "${CYAN}Building ${APP_NAME} macOS application...${RESET}"

# Clean up any existing build
if [ -d "${APP_BUNDLE}" ]; then
    echo -e "${YELLOW}Removing existing ${APP_BUNDLE}...${RESET}"
    rm -rf "${APP_BUNDLE}"
fi

# Create app bundle structure
echo -e "${CYAN}Creating app bundle structure...${RESET}"
mkdir -p "${MACOS_DIR}"
mkdir -p "${RESOURCES_DIR}"

# Create Info.plist
cat > "${APP_DIR}/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>${SCRIPT_NAME}</string>
    <key>CFBundleIdentifier</key>
    <string>com.pysuite.awake</string>
    <key>CFBundleName</key>
    <string>${APP_NAME}</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0.0</string>
    <key>CFBundleVersion</key>
    <string>1</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.13</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>LSUIElement</key>
    <true/>
    <key>NSHumanReadableCopyright</key>
    <string>Copyright © 2025 PySuite. All rights reserved.</string>
</dict>
</plist>
EOF

# Create launcher script
cat > "${MACOS_DIR}/${SCRIPT_NAME}" << 'EOF'
#!/bin/bash
# Launcher script for Awake app

# Get the directory where the app bundle is located
APP_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
RESOURCES_DIR="${APP_DIR}/Contents/Resources"

# Use bundled virtual environment if available, otherwise fallback to system Python
if [ -f "${RESOURCES_DIR}/venv/bin/python" ]; then
    PYTHON="${RESOURCES_DIR}/venv/bin/python"
elif [ -f "${APP_DIR}/../../venv/bin/python" ]; then
    PYTHON="${APP_DIR}/../../venv/bin/python"
else
    # Try to find Python 3
    PYTHON=$(which python3)
    if [ -z "$PYTHON" ]; then
        osascript -e 'display dialog "Python 3 is required but not found. Please rebuild the app with virtual environment bundled using: ./build.sh" buttons {"OK"} default button "OK" with icon stop'
        exit 1
    fi
fi

# Run the application with error logging
LOG_FILE="${HOME}/Library/Logs/Awake.log"
mkdir -p "$(dirname "$LOG_FILE")"

# Redirect output to log file and also show errors
exec "$PYTHON" "${RESOURCES_DIR}/menubar.py" >> "$LOG_FILE" 2>&1
EOF

chmod +x "${MACOS_DIR}/${SCRIPT_NAME}"

# Copy the Python script to Resources
echo -e "${CYAN}Copying application files...${RESET}"
cp menubar.py "${RESOURCES_DIR}/"

# Bundle dependencies
if [ "$QUIET" = true ]; then
    # Quiet mode: automatically bundle venv
    echo -e "${CYAN}Creating virtual environment in app bundle (quiet mode)...${RESET}"
    BUNDLE_VENV=true
else
    # Interactive mode: ask user
    read -p "Do you want to bundle a virtual environment with the app? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        BUNDLE_VENV=true
    else
        BUNDLE_VENV=false
    fi
fi

if [ "$BUNDLE_VENV" = true ]; then
    echo -e "${CYAN}Creating virtual environment in app bundle...${RESET}"
    python3 -m venv "${RESOURCES_DIR}/venv"
    "${RESOURCES_DIR}/venv/bin/pip" install --upgrade pip --quiet
    "${RESOURCES_DIR}/venv/bin/pip" install -r requirements.txt --quiet
    echo -e "${GREEN}✓ Virtual environment created in app bundle${RESET}"
else
    echo -e "${YELLOW}⚠ Skipping virtual environment bundling${RESET}"
    echo -e "${YELLOW}   Note: App will require Python 3 to be installed on the system${RESET}"
fi

echo -e "${GREEN}✓ ${APP_BUNDLE} created successfully!${RESET}"
echo -e "${CYAN}You can now:${RESET}"
echo -e "  1. Test the app: open ${APP_BUNDLE}"
echo -e "  2. Distribute it: zip ${APP_BUNDLE} and share it"
echo -e "  3. Install it: drag ${APP_BUNDLE} to /Applications"
