import sys
import os
import threading
import time
import webbrowser

# Set working directory to where the exe/script lives
if getattr(sys, 'frozen', False):
    # Running as PyInstaller bundle
    app_dir = os.path.dirname(sys.executable)
    os.chdir(app_dir)
    sys.path.insert(0, app_dir)
    # Also suppress stdout/stderr since we're windowed (console=False)
    # Otherwise print() calls can cause issues
    sys.stdout = open(os.devnull, 'w')
    sys.stderr = open(os.devnull, 'w')
else:
    # Running in development
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend"))

import uvicorn

HOST = "127.0.0.1"
PORT = 8000
URL = f"http://{HOST}:{PORT}"


def open_browser():
    """Wait for the server to start, then open the browser."""
    time.sleep(2)
    try:
        print(f"\n  Imaginaree is running at {URL}")
        print("  Close this window to stop the app.\n")
    except Exception:
        pass
    webbrowser.open(URL)


def main():
    # Open browser in a background thread after server starts
    threading.Thread(target=open_browser, daemon=True).start()

    # Run the server (blocks until killed)
    log_level = "critical" if getattr(sys, 'frozen', False) else "info"
    uvicorn.run("app.main:app", host=HOST, port=PORT, log_level=log_level)


if __name__ == "__main__":
    main()
