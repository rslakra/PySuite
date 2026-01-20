#!/usr/bin/env python3
"""Diagnostic script to check rumps setup"""

import sys
import os

print("=" * 60)
print("Awake Diagnostic Tool")
print("=" * 60)

# Check Python version
print(f"\n✓ Python version: {sys.version}")

# Check if rumps can be imported
try:
    import rumps

    print(f"✓ rumps imported successfully")
    print(
        f"✓ rumps version: {rumps.__version__ if hasattr(rumps, '__version__') else 'unknown'}"
    )
except ImportError as e:
    print(f"✗ Failed to import rumps: {e}")
    sys.exit(1)

# Check if we can create an app
try:
    print("\nTesting rumps.App creation...")
    app = rumps.App("Test", icon=None, template=None)
    print("✓ rumps.App created successfully")

    # Try setting title
    app.title = "TEST"
    print("✓ App title set to 'TEST'")

    print("\n" + "=" * 60)
    print("DIAGNOSIS: Rumps appears to be working correctly!")
    print("=" * 60)
    print("\nIf you still don't see icons, possible issues:")
    print("1. macOS may be hiding menubar icons (check System Preferences)")
    print("2. Menubar might be too crowded")
    print("3. Try running the app from Finder instead of terminal")
    print("4. Check Activity Monitor to see if Python processes are running")
    print("\nTry running: ./venv/bin/python awake/simple_test.py")
    print("Look for 'SLP' or 'TEST' in your menubar")
    print("=" * 60)

except Exception as e:
    print(f"✗ Error creating rumps.App: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)
