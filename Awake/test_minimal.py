#!/usr/bin/env python3
"""Minimal test to verify rumps works in app bundle context"""

import sys
import os

# Add path for debugging
print(f"Python: {sys.version}")
print(f"Python executable: {sys.executable}")
print(f"Current directory: {os.getcwd()}")

try:
    import rumps

    print("✓ rumps imported")

    class MinimalApp(rumps.App):
        def __init__(self):
            super(MinimalApp, self).__init__("TEST", icon=None, template=None)
            self.title = "●"
            self.menu = [
                rumps.MenuItem("Test - Click me!", callback=self.test),
                rumps.MenuItem("Quit", callback=rumps.quit_application),
            ]
            print("✓ App created")
            # Show notification
            try:
                rumps.notification("Test", "App Started", "Look for ● in menubar!")
                print("✓ Notification sent")
            except Exception as e:
                print(f"✗ Notification failed: {e}")

        def test(self, _):
            rumps.alert("Success!", "Rumps is working!")

    print("Starting app...")
    app = MinimalApp()
    print("Running app.run()...")
    app.run()

except Exception as e:
    print(f"✗ Error: {e}")
    import traceback

    traceback.print_exc()
    # Keep window open
    input("Press Enter to exit...")
    sys.exit(1)
