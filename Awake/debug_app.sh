#!/bin/bash
# Debug script to check if Awake app is working

echo "=== Awake Debug Information ==="
echo ""

# Check if app is running
echo "1. Checking if app is running..."
if ps aux | grep -i "awake\|awake_launcher" | grep -v grep > /dev/null; then
    echo "   ✓ App is running"
    ps aux | grep -i "awake\|awake_launcher" | grep -v grep
else
    echo "   ✗ App is NOT running"
fi

echo ""
echo "2. Checking log file..."
if [ -f ~/Library/Logs/Awake.log ]; then
    echo "   ✓ Log file exists"
    echo "   Last 10 lines:"
    tail -10 ~/Library/Logs/Awake.log
else
    echo "   ✗ Log file not found (app may not have started)"
fi

echo ""
echo "3. Checking if .app bundle exists..."
if [ -d "Awake.app" ]; then
    echo "   ✓ Awake.app exists"
    echo "   Info.plist LSUIElement:"
    grep -A 1 "LSUIElement" Awake.app/Contents/Info.plist || echo "   ✗ LSUIElement not found!"
else
    echo "   ✗ Awake.app not found"
fi

echo ""
echo "4. Testing rumps directly..."
cd "$(dirname "$0")"
if [ -f "../venv/bin/python" ]; then
    ../venv/bin/python -c "import rumps; app = rumps.App('TEST'); print('✓ Rumps works'); app.title = '●'; print('✓ Title set')" 2>&1
else
    echo "   ✗ Virtual environment not found"
fi

echo ""
echo "=== Debug Complete ==="
echo ""
echo "If app is running but no icon:"
echo "1. Check System Settings → Dock & Menu Bar"
echo "2. Try quitting and restarting the app"
echo "3. Check Console.app for errors"
echo "4. Try running: ./test_minimal.py to test rumps"
