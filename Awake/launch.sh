#!/bin/bash
# Launch script for Awake.app

cd "$(dirname "$0")"

echo "Launching Awake.app..."
echo "If you see a security warning, click 'Open'"
echo ""
echo "After launching, check:"
echo "1. Do you see a notification?"
echo "2. Look for ☕ icon in the RIGHT side of menubar"
echo "3. Check Activity Monitor for 'Awake' process"
echo ""

# Kill any existing instances
pkill -9 -f "awake_launcher\|menubar" 2>/dev/null

# Open the app
open Awake.app

sleep 2

# Check if it's running
if ps aux | grep -i "awake" | grep -v grep > /dev/null; then
    echo "✓ App is running!"
    echo "Look for the icon in your menubar (right side)"
else
    echo "✗ App failed to start. Check Console.app for errors."
fi
