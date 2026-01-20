#!/usr/bin/env python3
"""
Awake - Keep your Mac awake
A simple menubar app that prevents your Mac from automatically going to sleep,
dimming the screen, or starting screen savers.
"""

import rumps
import subprocess
import os
import sys
import signal


class AwakeApp(rumps.App):
    def __init__(self):
        # Initialize with blocked icon (inactive state)
        # Using simple symbols that render better in menubar
        # ⛔ = inactive (red-like, blocked), ✓ = active (green-like, allowed)
        # Use simple text that definitely renders
        super(AwakeApp, self).__init__("OFF", icon=None, template=None)
        self.active = False
        self.caffeinate_process = None
        # Start with inactive state - use simple text
        self.title = "OFF"
        self.update_menu()

    def update_menu(self):
        """Update the menubar icon and menu based on current state"""
        if self.active:
            self.title = "ON"  # Simple text when active
            self.menu.clear()
            self.menu = [
                rumps.MenuItem("Sleep prevention is ACTIVE", callback=None),
                rumps.separator,
                rumps.MenuItem("Deactivate", callback=self.toggle),
                rumps.separator,
                rumps.MenuItem("Quit", callback=self.quit_app),
            ]
        else:
            # Simple text when inactive
            self.title = "OFF"  # Simple text that should definitely render
            self.menu.clear()
            self.menu = [
                rumps.MenuItem("Sleep prevention is INACTIVE", callback=None),
                rumps.separator,
                rumps.MenuItem("Activate", callback=self.toggle),
                rumps.separator,
                rumps.MenuItem("Quit", callback=self.quit_app),
            ]

    def prevent_sleep(self):
        """Start caffeinate process to prevent sleep"""
        # caffeinate flags:
        # -i: prevent idle sleep
        # -d: prevent display sleep
        # -m: prevent disk sleep
        # -s: prevent system sleep
        # -w: wait for process (we'll use -w with our own PID to keep it running)
        try:
            # Use caffeinate with flags to prevent all types of sleep
            # -i: prevent idle sleep
            # -d: prevent display from sleeping
            # -m: prevent disk from sleeping
            # -s: prevent system from sleeping
            # -w: wait for specified process (we use our own PID)
            self.caffeinate_process = subprocess.Popen(
                ["caffeinate", "-i", "-d", "-m", "-s", "-w", str(os.getpid())],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            # Also prevent network disconnection by keeping network interfaces active
            # This is handled by caffeinate -i flag
            return True
        except Exception as e:
            rumps.alert("Error", f"Failed to prevent sleep: {str(e)}")
            return False

    def allow_sleep(self):
        """Stop caffeinate process to allow sleep"""
        if self.caffeinate_process:
            try:
                self.caffeinate_process.terminate()
                self.caffeinate_process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.caffeinate_process.kill()
            except Exception as e:
                print(f"Error stopping caffeinate: {e}")
            finally:
                self.caffeinate_process = None

    @rumps.clicked("Enable")
    def enable(self, _):
        """Enable sleep prevention"""
        self.toggle(_)

    @rumps.clicked("Disable")
    def disable(self, _):
        """Disable sleep prevention"""
        self.toggle(_)

    def toggle(self, _):
        """Toggle sleep prevention on/off"""
        if self.active:
            self.allow_sleep()
            self.active = False
            rumps.notification(
                "Awake",
                "Deactivated",
                "Your Mac can now sleep normally",
            )
        else:
            if self.prevent_sleep():
                self.active = True
                rumps.notification("Awake", "Activated", "Your Mac will stay awake")
            else:
                rumps.alert("Error", "Failed to enable sleep prevention")
        self.update_menu()

    def quit_app(self, _):
        """Clean up and quit the application"""
        if self.active:
            self.allow_sleep()
        rumps.quit_application()

    def cleanup(self):
        """Cleanup on exit"""
        if self.active:
            self.allow_sleep()


def main():
    """Main entry point"""
    import logging

    # Set up logging to file
    log_file = os.path.expanduser("~/Library/Logs/Awake.log")
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    logging.basicConfig(
        filename=log_file,
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    try:
        print("=" * 60)
        print("Awake - Keep your Mac awake")
        print("=" * 60)
        print("\n📍 Look for the 🚫 or ✅ icon in the RIGHT side of your menubar")
        print("   (near the clock, battery, WiFi icons)")
        print("\n💡 Click to toggle - ✅ (green) = active, 🚫 (red) = inactive")
        print("\n⚠️  Note: The app runs in the background.")
        print("   To quit, click the icon and select 'Quit'")
        print("=" * 60)
        print("\nStarting app...\n")
        logging.info("Starting Awake app")

        app = AwakeApp()
        logging.info("AwakeApp created successfully")
        logging.info(f"App title: {app.title}")

        # Force title update after a brief delay to ensure status item is ready
        import time

        time.sleep(0.2)
        app.title = app.title  # Force update
        logging.info("Title forced update")

        # Show notification to confirm app started
        try:
            rumps.notification(
                "Awake",
                "App Started",
                "Look for 🚫 or ✅ icon in the right side of your menubar!",
            )
            logging.info("Notification sent")
        except Exception as e:
            logging.error(f"Could not show notification: {e}")
            print(f"Note: Could not show notification: {e}")

        # Handle cleanup on termination
        def signal_handler(sig, frame):
            logging.info("Received signal, cleaning up")
            app.cleanup()
            sys.exit(0)

        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)

        logging.info("Starting app.run()")
        app.run()
        logging.info("App.run() completed")
    except Exception as e:
        error_msg = f"Fatal error: {e}"
        logging.error(error_msg, exc_info=True)
        print(error_msg)
        import traceback

        traceback.print_exc()
        # Show error dialog
        try:
            rumps.alert(
                "Awake Error",
                f"Failed to start: {e}\n\nCheck ~/Library/Logs/Awake.log for details",
            )
        except:
            pass
        sys.exit(1)
    finally:
        try:
            app.cleanup()
        except:
            pass


if __name__ == "__main__":
    main()
