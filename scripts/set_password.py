#!/usr/bin/env python3
"""Set the Imaginaree sign-in password (stored hashed in .env).

Usage:  python scripts/set_password.py
"""
import getpass
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from app.passwords import MIN_PASSWORD_LENGTH, hash_password  # noqa: E402

ENV_FILE = ROOT / ".env"


def set_env_value(key: str, value: str) -> None:
    lines = ENV_FILE.read_text().splitlines() if ENV_FILE.exists() else []
    entry = f"{key}='{value}'"
    pattern = re.compile(rf"^\s*{re.escape(key)}\s*=")
    for i, line in enumerate(lines):
        if pattern.match(line):
            lines[i] = entry
            break
    else:
        lines.append(entry)
    fd = os.open(ENV_FILE, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        f.write("\n".join(lines) + "\n")
    os.chmod(ENV_FILE, 0o600)


def main() -> int:
    print("Choose a password for Imaginaree.")
    print(f"Use a long passphrase ({MIN_PASSWORD_LENGTH}+ characters): this is all that protects the app.\n")
    password = getpass.getpass("New password: ")
    if len(password) < MIN_PASSWORD_LENGTH:
        print(f"Too short: use at least {MIN_PASSWORD_LENGTH} characters.")
        return 1
    if getpass.getpass("Repeat password: ") != password:
        print("Passwords didn't match.")
        return 1

    set_env_value("APP_PASSWORD_HASH", hash_password(password))
    print(f"\nSaved to {ENV_FILE}")
    print("Everyone is signed out. Restart Imaginaree for the change to apply:")
    print("  systemctl --user restart imaginaree")
    return 0


if __name__ == "__main__":
    sys.exit(main())
