# Steps to Rebuild and Test

Since the app is running but the icon isn't visible, follow these steps:

## 1. Rebuild the App

```bash
cd awake
./build.sh
# Answer 'y' when asked about bundling venv
```

## 2. Check for Hidden Menu Bar Items

macOS may be hiding the icon. Check:
- **System Settings → Dock & Menu Bar**
- Look for "Menu Bar Extras" or hidden items
- Some icons might be in a "..." overflow menu if your menubar is crowded

## 3. Try Running with Console Visible

Open Console.app (Applications → Utilities) and filter for "Awake" to see any errors.

## 4. Check the Log File

After rebuilding and running, check:
```bash
./check_logs.sh
# Or manually:
tail -f ~/Library/Logs/Awake.log
```

## 5. Alternative: Try PyInstaller

If the .app bundle still doesn't work, try PyInstaller which creates a more self-contained app:

```bash
pip install pyinstaller
pyinstaller awake.spec
open dist/Awake.app
```

## 6. Test with Minimal App

Test if rumps works at all in app bundle context:
```bash
# Copy test_minimal.py to app bundle and test
```

## Common Issues

1. **Icon is hidden by macOS** - Check System Settings
2. **App crashes silently** - Check Console.app and log file
3. **Python version mismatch** - The bundled venv might have wrong Python version
4. **Permissions** - macOS might be blocking the app
