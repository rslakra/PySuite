#!/usr/bin/env python3
"""Test with very simple text icon to see if rumps title works"""

import rumps
import sys


class SimpleIconApp(rumps.App):
    def __init__(self):
        # Try with simple text first
        super(SimpleIconApp, self).__init__("SLP", icon=None, template=None)
        self.title = "SLP"  # Simple text
        self.menu = [
            rumps.MenuItem("Test - Click me!", callback=self.test),
            rumps.MenuItem("Quit", callback=rumps.quit_application),
        ]
        print("App created with title: SLP")
        # Force update
        rumps.notification("Test", "App Started", "Look for 'SLP' in menubar!")

    def test(self, _):
        rumps.alert("Found it!", "You found the menubar icon!")


if __name__ == "__main__":
    print("Starting simple icon test...")
    print("If you see 'SLP' in menubar, rumps title works")
    try:
        app = SimpleIconApp()
        app.run()
    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
