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
    # Redirect stdout/stderr to a log file so we can debug issues
    log_file = os.path.join(app_dir, 'imaginaree.log')
    sys.stdout = open(log_file, 'w', buffering=1)
    sys.stderr = sys.stdout
else:
    # Running in development
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend"))

import uvicorn

from app.auth import assert_safe_config
from app.config import settings


def open_browser(url: str):
    """Wait for the server to start, then open the browser."""
    time.sleep(2)
    try:
        print(f"\n  Imaginaree is running at {url}\n")
    except Exception:
        pass
    webbrowser.open(url)


def main():
    try:
        assert_safe_config()
    except RuntimeError as exc:
        print(f"\n  {exc}\n")
        sys.exit(1)

    host, port = settings.APP_HOST, settings.APP_PORT
    if settings.OPEN_BROWSER:
        url = f"http://{'127.0.0.1' if host in ('0.0.0.0', '::') else host}:{port}"
        threading.Thread(target=open_browser, args=(url,), daemon=True).start()

    # Run the server (blocks until killed)
    uvicorn.run("app.main:app", host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()
