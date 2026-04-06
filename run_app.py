import sys
import os
import threading
import time

# Set working directory to where the exe/script lives
if getattr(sys, 'frozen', False):
    os.chdir(os.path.dirname(sys.executable))
    sys.path.insert(0, os.path.dirname(sys.executable))
else:
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend"))

import uvicorn
import webview

HOST = "127.0.0.1"
PORT = 8000


def start_server():
    """Run the FastAPI server in a background thread."""
    uvicorn.run("app.main:app", host=HOST, port=PORT, log_level="info")


def main():
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    # Give the server a moment to start
    time.sleep(2)

    window = webview.create_window(
        title="Imaginaree",
        url=f"http://{HOST}:{PORT}",
        width=1400,
        height=900,
        min_size=(800, 600),
    )
    webview.start()


if __name__ == "__main__":
    main()
