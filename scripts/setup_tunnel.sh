#!/usr/bin/env bash
# Connects Imaginaree to your Cloudflare Tunnel so it's reachable at your own domain.
# Create the tunnel first (see docs/REMOTE_ACCESS_LINUX.md), then run this and paste its token.
#
# Usage:  bash scripts/setup_tunnel.sh
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BIN_DIR="$HOME/.local/bin"
CONF_DIR="$HOME/.config/imaginaree"
UNIT_DIR="$HOME/.config/systemd/user"

say() { printf '\n==> %s\n' "$*"; }
die() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }

command -v systemctl >/dev/null || die "systemd is required."
mkdir -p "$BIN_DIR" "$CONF_DIR" "$UNIT_DIR"

CLOUDFLARED="$(command -v cloudflared || true)"
if [ -z "$CLOUDFLARED" ]; then
  say "Downloading cloudflared"
  case "$(uname -m)" in
    x86_64)  file=cloudflared-linux-amd64 ;;
    aarch64) file=cloudflared-linux-arm64 ;;
    *) die "Unsupported CPU: $(uname -m)" ;;
  esac
  curl -fL "https://github.com/cloudflare/cloudflared/releases/latest/download/$file" -o "$BIN_DIR/cloudflared"
  chmod +x "$BIN_DIR/cloudflared"
  CLOUDFLARED="$BIN_DIR/cloudflared"
fi
echo "Using $CLOUDFLARED"

say "Tunnel token"
echo "Paste the token from the Cloudflare dashboard (input is hidden), then press Enter."
read -rsp "Token: " token
echo
[ -n "$token" ] || die "No token entered."
( umask 077; printf 'TUNNEL_TOKEN=%s\n' "$token" > "$CONF_DIR/cloudflared.env" )

say "Installing the tunnel service"
sed "s|@CLOUDFLARED@|$CLOUDFLARED|g" "$APP_DIR/scripts/cloudflared-imaginaree.service" \
  > "$UNIT_DIR/cloudflared-imaginaree.service"
systemctl --user daemon-reload
systemctl --user enable cloudflared-imaginaree.service
systemctl --user restart cloudflared-imaginaree.service
sleep 3
systemctl --user --no-pager --lines=5 status cloudflared-imaginaree.service || true

PORT="$(grep -E '^APP_PORT=' "$APP_DIR/.env" 2>/dev/null | tail -1 | cut -d= -f2 | tr -d "'\" ")"
printf '\nDone. Open your domain in a browser and sign in.\n'
printf 'In Cloudflare, the tunnel route'"'"'s Service URL must be http://127.0.0.1:%s\n' "${PORT:-8000}"
