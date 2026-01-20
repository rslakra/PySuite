#!/usr/bin/env python3
"""Visible test with notification to confirm it's running"""

import rumps
import sys


class VisibleApp(rumps.App):
    def __init__(self):
        # Use a very visible text
        super(VisibleApp, self).__init__("●", icon=None, template=None)
        self.menu = [
            rumps.MenuItem("I AM HERE - Click me!", callback=self.show_alert),
            rumps.MenuItem("Quit", callback=rumps.quit_application),
        ]
        # Show notification when app starts
        rumps.notification(
            "Awake Test",
            "App Started",
            "Look for a black circle (●) in your menubar!",
        )

    def show_alert(self, _):
        rumps.alert("Found it!", "You found the menubar icon! It's working correctly.")


if __name__ == "__main__":
    print("=" * 60)
    print("Starting visible test app...")
    print("You should see:")
    print("1. A notification popup")
    print("2. A black circle (●) in your menubar (right side)")
    print("3. Click it to see a menu")
    print("=" * 60)
    print("\nIf you don't see the icon, check:")
    print("- Right side of menubar (near clock/battery)")
    print("- Activity Monitor for Python processes")
    print("- System Preferences > Dock & Menu Bar")
    print("=" * 60)

    try:
        app = VisibleApp()
        app.run()
    except KeyboardInterrupt:
        print("\nQuitting...")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
