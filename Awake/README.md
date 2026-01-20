# Awake - macOS Menubar Sleep Prevention App

A macOS menubar application that prevents your Mac from automatically going to sleep, dimming the screen, starting screen savers, and disconnecting from networks.

## Features

- 🌙 **Menubar Icon**: Always visible in your menubar
- ☕/🌙 **Visual Status**: Icon changes to show active/inactive state
- ⚡ **One-Click Toggle**: Enable/disable sleep prevention with a single click
- 🔒 **Prevents**:
  - System sleep
  - Display sleep/dimming
  - Screen savers
  - Network disconnection
  - Disk sleep

## Quick Start

### 1. Install Dependencies

From the project root:

```bash
# Install Awake-specific dependencies
just install-awake

# Or install all project dependencies
just install-packages
```

### 2. Run the App

**Important:** macOS may not show menubar icons for Python scripts run directly from terminal. Use the .app bundle instead:

```bash
# Build the app bundle (first time only)
cd awake
chmod +x build.sh
./build.sh
# Answer 'y' when asked about bundling venv

# Or use quiet mode to automatically bundle venv:
./build.sh --quiet

# Open the app
open awake/Awake.app
```

Or use the Justfile command:
```bash
just build-awake
open awake/Awake.app
```

**Alternative (for development/testing):**
```bash
just run-awake
# Note: Icon may not appear when run from terminal
```

### 3. Use the App

1. Look for the **☕** icon in your menubar (right side)
2. Click the icon to open the menu
3. Click **"Enable"** to prevent sleep
4. The icon changes to **🌙** when active
5. Click **"Disable"** to allow normal sleep behavior

#### Where to Find the Icon

The Awake icon appears in the **RIGHT side** of your macOS menubar, near:
- Clock
- Battery indicator
- WiFi signal
- Bluetooth
- Volume control
- Other system icons

**Visual Guide:**
```
┌─────────────────────────────────────────────────────────────┐
│  Apple  File  Edit  View  ...  [App Icons]  ☕  🔋  📶  🕐   │
│                                 ↑                           │
│                            Look here!                       │
└─────────────────────────────────────────────────────────────┘
```

**Icon Appearance:**
- **☕** (coffee cup) - When sleep prevention is **INACTIVE**
- **🌙** (moon) - When sleep prevention is **ACTIVE**

## How It Works

The app uses macOS's built-in `caffeinate` command with the following flags:
- `-i`: Prevent idle sleep
- `-d`: Prevent display from sleeping
- `-m`: Prevent disk from sleeping
- `-s`: Prevent system from sleeping
- `-w`: Wait for process (keeps it running)

When enabled, it runs `caffeinate` in the background. When disabled, it terminates the process, allowing normal sleep behavior.

## Building for Distribution

This guide explains how to build and distribute the Awake menubar application as a standalone macOS `.app` bundle that others can use.

### Prerequisites

1. **macOS** (10.13 or later)
2. **Python 3.12+** installed
3. **Dependencies** installed:
   ```bash
   pip install -r requirements.txt
   ```

### Quick Build

**Option 1: Using build script**
```bash
just build-awake
```

**Option 1b: Using build script with quiet mode** (automatically bundles venv)
```bash
cd awake
./build.sh --quiet
# or
./build.sh -q
```

**Option 2: Using PyInstaller** (recommended for distribution)
```bash
pip install pyinstaller
just build-awake-pyinstaller
```

### Building Methods

#### Method 1: Using the Build Script (Recommended)

1. Navigate to the awake directory:
   ```bash
   cd awake
   ```

2. Make the build script executable:
   ```bash
   chmod +x build.sh
   ```

3. Run the build script:

   **Interactive mode** (prompts for venv bundling):
   ```bash
   ./build.sh
   # Answer 'y' when asked about bundling venv
   ```

   **Quiet mode** (automatically bundles venv, no prompts):
   ```bash
   ./build.sh --quiet
   # or
   ./build.sh -q
   ```

The script will:
- Create the `Awake.app` bundle structure
- Copy necessary files
- Optionally create a bundled virtual environment (interactive mode asks, quiet mode always bundles)
- Set proper permissions

#### Method 2: Standalone App (No Python Required)

For users who don't have Python installed, you can bundle everything:

1. **Build with virtual environment:**

   **Interactive mode:**
   ```bash
   ./build.sh
   # Answer 'y' when asked about bundling venv
   ```

   **Quiet mode** (recommended for automation):
   ```bash
   ./build.sh --quiet
   # Automatically bundles venv without prompting
   ```

2. **Test the app:**
   ```bash
   open Awake.app
   ```

3. **Create a distributable archive:**
   ```bash
   zip -r Awake-v1.0.0.zip Awake.app
   ```

#### Method 3: Using PyInstaller (Recommended for Distribution)

PyInstaller creates a more self-contained app:

1. **Install PyInstaller:**
   ```bash
   pip install pyinstaller
   ```

2. **Build with PyInstaller** (from project root):
   ```bash
   pyinstaller awake/awake.spec
   ```

3. **The app will be in `dist/Awake.app`**

The spec file (`awake.spec`) is already configured with:
- Hidden imports for `rumps`
- Proper bundle identifier
- LSUIElement set to true (hides from Dock)
- High resolution support

#### Method 4: Using py2app

1. **Install py2app:**
   ```bash
   pip install py2app
   ```

2. **Create setup.py:**
   ```python
   from setuptools import setup

   APP = ['menubar_sleepless.py']
   DATA_FILES = []
   OPTIONS = {
       'argv_emulation': False,
       'plist': {
           'LSUIElement': True,
           'NSHighResolutionCapable': True,
       },
       'packages': ['rumps'],
   }

   setup(
       app=APP,
       data_files=DATA_FILES,
       options={'py2app': OPTIONS},
       setup_requires=['py2app'],
   )
   ```

3. **Build:**
   ```bash
   python setup.py py2app
   ```

### Manual Build

1. **Create the app bundle structure:**
   ```bash
   mkdir -p Awake.app/Contents/{MacOS,Resources}
   ```

2. **Create Info.plist** (see `build.sh` for example)

3. **Create launcher script** in `Awake.app/Contents/MacOS/sleepless_launcher`:
   ```bash
   # Make it executable: chmod +x
   ```

4. **Copy Python script:**
   ```bash
   cp menubar_sleepless.py Awake.app/Contents/Resources/
   ```

## Code Signing (Optional but Recommended)

For distribution outside the App Store, you should code sign your app:

1. **Get a Developer ID from Apple** (free for personal use, paid for distribution)

2. **Sign the app:**
   ```bash
   codesign --deep --force --verify --verbose --sign "Developer ID Application: Your Name" Awake.app
   ```

3. **Verify signing:**
   ```bash
   codesign --verify --verbose Awake.app
   ```

## Notarization (For macOS 10.15+)

If distributing outside the App Store, you may need to notarize:

1. **Create an app-specific password** in Apple ID settings

2. **Notarize:**
   ```bash
   xcrun altool --notarize-app \
     --primary-bundle-id "com.pysuite.awake" \
     --username "your@email.com" \
     --password "app-specific-password" \
     --file Awake.zip
   ```

## Distribution Checklist

- [ ] Test the app on a clean macOS installation
- [ ] Verify all dependencies are included
- [ ] Test enable/disable functionality
- [ ] Test quit functionality
- [ ] Code sign the app (optional)
- [ ] Create a zip archive
- [ ] Write release notes
- [ ] Test the downloaded app on another Mac

## User Installation Instructions

Include these instructions for end users:

1. **Download** the `Awake.app` or `Awake.zip` file

2. **Extract** (if zipped):
   ```bash
   unzip Awake.zip
   ```

3. **Move to Applications** (optional):
   ```bash
   mv Awake.app /Applications/
   ```

4. **First-time run** (if not code signed):
   - Right-click the app
   - Select "Open"
   - Click "Open" in the security dialog

5. **Launch the app:**
   - Double-click `Awake.app`
   - Look for the ☕ or 🌙 icon in the menubar

6. **Usage:**
   - Click the menubar icon
   - Select "Enable" to prevent sleep
   - Select "Disable" to allow sleep
   - Select "Quit" to exit

## Troubleshooting

### App won't start
- Make sure you've activated the virtual environment
- Check that `rumps` is installed: `pip list | grep rumps`
- Try running directly: `python awake/menubar_sleepless.py`
- Check macOS security settings
- Right-click and select "Open" to bypass Gatekeeper
- Verify Python 3 is installed (if not using bundled version)

### Icon doesn't appear

**Important:** macOS may not show menubar icons for Python scripts run directly from terminal. **You MUST use the .app bundle** for the icon to appear reliably.

**Where to look:**
- The icon appears in the **RIGHT side** of the menubar (near clock, battery, WiFi icons)
- Look for the ☕ emoji icon

**Solution: Use the .app Bundle**

1. **Build the app bundle:**
   ```bash
   cd awake
   chmod +x build.sh
   ./build.sh
   # Answer 'y' when asked about bundling venv
   # Or use: ./build.sh --quiet (automatically bundles venv)
   ```

2. **Open the app from Finder:**
   - Navigate to `awake/Awake.app`
   - Double-click to open
   - If you see a security warning, right-click → Open, then click "Open"

3. **The icon should now appear in your menubar!**

**Why this happens:**
- macOS treats Python scripts run from terminal differently than proper .app bundles
- Menubar icons require the app to be recognized as a GUI application
- .app bundles have proper Info.plist configuration (`LSUIElement` key) that tells macOS to show the menubar icon

**Additional troubleshooting:**

1. **Check if the app is running:**
   ```bash
   ps aux | grep menubar_sleepless
   # Or check Activity Monitor for "Awake" or "Python" processes
   ```

2. **Check System Settings:**
   - System Settings → Dock & Menu Bar
   - Look for any hidden menu bar items
   - System Settings → Privacy & Security → Accessibility
   - Make sure the app has necessary permissions

3. **Check menubar space:**
   - If your menubar is crowded, some icons might be hidden
   - Try quitting other menubar apps temporarily
   - macOS may hide icons if there's not enough space

4. **Check Console.app for errors:**
   - Open Console.app (Applications → Utilities)
   - Look for errors related to Awake or Python

**Icon shows as text instead of emoji?**
- Some macOS versions or font settings might not display emojis properly
- The icon should still be clickable even if it shows as text
- Try updating macOS or checking your font settings

### Sleep prevention doesn't work
- Make sure you clicked "Enable" in the menu
- Check that the icon shows 🌙 (active state)
- Verify `caffeinate` works in Terminal: `caffeinate -i -d -m -s`
- Check System Preferences > Security & Privacy > Privacy > Accessibility
- Grant necessary permissions if prompted

### Permission issues
- macOS may require Accessibility permissions
- Go to System Preferences > Security & Privacy > Privacy > Accessibility
- Add Terminal or Python if prompted

## Requirements

- macOS 10.13 or later
- Python 3.12+
- `rumps` library (installed via `awake/requirements.txt`)

## Files

- `menubar_sleepless.py` - Main application code
- `build.sh` - Script to build macOS .app bundle
- `launch.sh` - Script to launch the Awake.app
- `awake.spec` - PyInstaller specification file
- `requirements.txt` - Awake-specific dependencies

## Version History

- **v1.0.0** - Initial release
  - Basic sleep prevention
  - Menubar interface
  - Enable/disable toggle

## License

[Add your license here]
