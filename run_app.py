import sys
import os
import threading
import time
import webbrowser

# Set working directory to where the exe/script lives
if getattr(sys, 'frozen', False):
    os.chdir(os.path.dirname(sys.executable))
    sys.path.insert(0, os.path.dirname(sys.executable))
else:
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend"))

import uvicorn

HOST = "127.0.0.1"
PORT = 8000
URL = f"http://{HOST}:{PORT}"


def open_browser():
    """Wait for the server to start, then open the browser."""
    time.sleep(2)
    print(f"\n  Imaginaree is running at {URL}")
    print("  Close this window to stop the app.\n")
    webbrowser.open(URL)


def main():
    # Open browser in a background thread after server starts
    threading.Thread(target=open_browser, daemon=True).start()

    # Run the server (blocks until killed)
    uvicorn.run("app.main:app", host=HOST, port=PORT, log_level="info")


if __name__ == "__main__":
    main()
