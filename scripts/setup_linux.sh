#!/usr/bin/env bash
# Sets up Imaginaree on Linux and runs it as a background service.
# Written for Bazzite / Fedora Atomic with an NVIDIA GPU, but works on most distros.
#
# Usage:  bash scripts/setup_linux.sh
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="$APP_DIR/backend/venv"
UNIT_DIR="$HOME/.config/systemd/user"

say()  { printf '\n==> %s\n' "$*"; }
warn() { printf 'WARNING: %s\n' "$*" >&2; }
die()  { printf 'ERROR: %s\n' "$*" >&2; exit 1; }

command -v python3 >/dev/null || die "python3 not found."
python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' \
  || die "Python 3.10 or newer is required (found $(python3 --version))."
command -v systemctl >/dev/null || die "systemd is required."

say "Checking the GPU"
if command -v nvidia-smi >/dev/null 2>&1; then
  nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader
else
  warn "nvidia-smi not found. Without an NVIDIA GPU, image generation will be very slow."
fi

say "Creating the Python environment ($VENV)"
if [ ! -x "$VENV/bin/python" ]; then
  python3 -m venv "$VENV" || die "Could not create a virtual environment. On Bazzite you can run this inside 'distrobox enter' instead."
fi
"$VENV/bin/python" -m pip install --quiet --upgrade pip

say "Installing packages (the first time this downloads several GB)"
# On Linux the default PyTorch wheel already includes CUDA support.
# To use a specific build instead: TORCH_INDEX_URL=https://download.pytorch.org/whl/cu128 bash scripts/setup_linux.sh
if [ -n "${TORCH_INDEX_URL:-}" ]; then
  "$VENV/bin/pip" install torch --index-url "$TORCH_INDEX_URL"
fi
"$VENV/bin/pip" install -r "$APP_DIR/backend/requirements.txt"
"$VENV/bin/pip" install -r "$APP_DIR/backend/requirements-flux.txt" \
  || warn "Could not install bitsandbytes. Everything works except the FLUX model."

say "Checking that PyTorch can see the GPU"
if ! "$VENV/bin/python" - <<'PY'
import sys, torch
print("PyTorch", torch.__version__)
if not torch.cuda.is_available():
    print("CUDA is NOT available: images would be generated on the CPU.")
    sys.exit(1)
print("GPU:", torch.cuda.get_device_name(0))
PY
then
  warn "PyTorch can't use the GPU. Check 'nvidia-smi', or install a different build with TORCH_INDEX_URL."
fi

say "Configuring"
if [ ! -f "$APP_DIR/.env" ]; then
  cp "$APP_DIR/.env.example" "$APP_DIR/.env"
  chmod 600 "$APP_DIR/.env"
fi
if ! grep -Eq "^APP_PASSWORD_HASH='.+'" "$APP_DIR/.env"; then
  "$VENV/bin/python" "$APP_DIR/scripts/set_password.py"
fi

say "Choosing a port"
# Stop our own service first so it doesn't count as "in use" when re-running this script.
systemctl --user stop imaginaree.service 2>/dev/null || true
PORT="$(grep -E '^APP_PORT=' "$APP_DIR/.env" | tail -1 | cut -d= -f2 | tr -d "'\" ")"
PORT="${PORT:-8000}"
port_in_use() {
  python3 -c 'import socket, sys
s = socket.socket()
s.settimeout(1)
sys.exit(0 if s.connect_ex(("127.0.0.1", int(sys.argv[1]))) == 0 else 1)' "$1"
}
while port_in_use "$PORT"; do
  warn "Port $PORT is already used by another program."
  PORT=$((PORT + 1))
done
if grep -q '^APP_PORT=' "$APP_DIR/.env"; then
  sed -i "s/^APP_PORT=.*/APP_PORT=$PORT/" "$APP_DIR/.env"
else
  echo "APP_PORT=$PORT" >> "$APP_DIR/.env"
fi
echo "Imaginaree will use port $PORT"

say "Installing the background service"
mkdir -p "$UNIT_DIR"
sed "s|@APP_DIR@|$APP_DIR|g" "$APP_DIR/scripts/imaginaree.service" > "$UNIT_DIR/imaginaree.service"
systemctl --user daemon-reload
systemctl --user enable imaginaree.service
# A service that failed repeatedly is refused further starts until reset.
systemctl --user reset-failed imaginaree.service 2>/dev/null || true
systemctl --user restart imaginaree.service
# Lets the service start at boot, before you log in.
loginctl enable-linger "$USER" || warn "Could not enable lingering; the app will only run while you're logged in."

say "Waiting for the app to start (loading PyTorch takes a moment)"
for _ in $(seq 1 60); do
  # Check for Imaginaree's own reply, not just any web server on the port.
  if curl -fsS "http://127.0.0.1:$PORT/api/auth/status" 2>/dev/null | grep -q auth_required; then
    printf '\nImaginaree is running: http://127.0.0.1:%s\n' "$PORT"
    printf 'Next, for access from anywhere: bash scripts/setup_tunnel.sh\n'
    printf '(In Cloudflare, the tunnel service URL must be http://localhost:%s)\n' "$PORT"
    exit 0
  fi
  sleep 2
done
die "The app didn't start. See why with:  journalctl --user -u imaginaree -n 50 --no-pager"
