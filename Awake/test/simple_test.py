#!/usr/bin/env python3
"""Very simple test to see if rumps menubar works"""

import rumps
import sys

print("Starting simple rumps test...")
print("If you see 'SLP' in your menubar, rumps is working!")


class SimpleApp(rumps.App):
    def __init__(self):
        # Try with text first instead of emoji
        super(SimpleApp, self).__init__("SLP", icon=None, template=None)
        self.menu = [
            rumps.MenuItem("Test - Click me!", callback=self.test_click),
            rumps.MenuItem("Quit", callback=rumps.quit_application),
        ]
        print("App initialized. Look for 'SLP' in menubar!")

    def test_click(self, _):
        rumps.alert("Success!", "Rumps is working! You clicked the menu item.")


if __name__ == "__main__":
    try:
        app = SimpleApp()
        print("Running app...")
        app.run()
    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
