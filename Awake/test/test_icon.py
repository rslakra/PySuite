#!/usr/bin/env python3
"""Quick test to verify rumps and menubar icon work"""

import rumps
import sys


class TestApp(rumps.App):
    def __init__(self):
        super(TestApp, self).__init__("Test", icon=None, template=None)
        self.title = "☕"  # Should appear in menubar
        self.menu = [
            rumps.MenuItem("Test Menu", callback=None),
            rumps.MenuItem("Quit", callback=rumps.quit_application),
        ]


if __name__ == "__main__":
    print("Starting test app...")
    print("Look for ☕ icon in the RIGHT side of your menubar (near clock/battery)")
    print("Press Ctrl+C to quit")
    try:
        app = TestApp()
        app.run()
    except KeyboardInterrupt:
        print("\nQuitting...")
        sys.exit(0)
