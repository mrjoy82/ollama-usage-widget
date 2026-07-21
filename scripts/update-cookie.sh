#!/usr/bin/env bash
# Convenience script to update the Ollama session cookie on the Pi.
# Usage: ./scripts/update-cookie.sh
# It will prompt for the cookie, write it securely, and restart the scraper.

set -euo pipefail

COOKIE_DIR="$HOME/.config/ollama-widget"
COOKIE_FILE="$COOKIE_DIR/cookie.txt"

echo "Ollama Cookie Update"
echo "===================="
echo ""
echo "1. Open https://ollama.com/settings in your desktop browser"
echo "2. Open DevTools (F12) → Application/Storage → Cookies → ollama.com"
echo "3. Copy the full _ollama_session cookie value"
echo ""

read -rp "Paste the cookie value (or the full Cookie header string): " cookie

if [[ -z "$cookie" ]]; then
    echo "ERROR: No cookie provided. Aborting." >&2
    exit 1
fi

mkdir -p "$COOKIE_DIR"
echo "$cookie" > "$COOKIE_FILE"
chmod 600 "$COOKIE_FILE"
chown "$(whoami):$(whoami)" "$COOKIE_FILE" 2>/dev/null || true

echo ""
echo "Cookie saved to $COOKIE_FILE (mode 600)"

# Restart scraper if it's running via systemd
if systemctl is-active --quiet ollama-widget-scraper 2>/dev/null; then
    echo "Restarting ollama-widget-scraper..."
    sudo systemctl restart ollama-widget-scraper
    echo "Done."
else
    echo "Note: ollama-widget-scraper service not running (expected during prototype)."
    echo "Start it with: python3 pi/scraper/scraper.py  (prototype)"
    echo "Or: sudo systemctl start ollama-widget-scraper  (production)"
fi
