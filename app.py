import argparse
from ui.ui_desktop import PasswordManagerApp
from ui.ui_web import start_web_server


def main() -> None:
    """Entry point for the password manager application."""
    print("Starting Password Manager...")
    parser = argparse.ArgumentParser(description="Secure local password manager")
    parser.add_argument(
        "--web",
        action="store_true",
        help="Start the optional local web interface for browser / iPhone access.",
    )
    args = parser.parse_args()

    try:
        if args.web:
            print("Launching web interface...")
            # Launch the web UI instead of the desktop UI.
            start_web_server()
        else:
            print("Initializing desktop app...")
            # Launch the local desktop password manager.
            app = PasswordManagerApp()
            print("Running mainloop...")
            app.run()
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()
