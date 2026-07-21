#!/usr/bin/env bash
# macbook-sync-cookie.sh
# Run this on your MacBook when the Ollama cookie expires.
# It prompts for the cookie value from Chrome DevTools, copies it to the Pi,
# sets permissions, and restarts the scraper.
#
# Prerequisites:
#   - 'TAgent' SSH alias works from this MacBook
#   - You are logged into Tailscale
#   - The Pi has the ollama-widget-scraper systemd service (or you are in prototype mode)
#
# Usage:
#   chmod +x macbook-sync-cookie.sh
#   ./macbook-sync-cookie.sh

set -euo pipefail

PI_HOST="TAgent"
PI_PATH="/home/matthieu/.config/ollama-widget/cookie.txt"

echo "Ollama Cookie Sync: MacBook → Pi"
echo "================================="
echo ""
echo "HOW TO COPY THE COOKIE FROM CHROME:"
echo ""
echo "  1. Open Chrome and go to: https://ollama.com/settings"
echo "  2. Make sure you are LOGGED IN (the page should show your usage)"
echo "  3. Press F12 (or right-click anywhere → Inspect)"
echo "  4. Click the 'Application' tab at the top of DevTools"
echo "  5. In the left sidebar, expand: Cookies → https://ollama.com"
echo "  6. Look for the row with Name: _ollama_session"
echo "  7. Click that row, then double-click the VALUE column"
echo "  8. The value is a long random string (may be 100+ characters)"
echo "  9. Copy it with Cmd+C"
echo ""
echo "Paste that value below — just the long random string, no quotes,"
echo "no 'name=' prefix. The script will format it for the Pi."
echo ""

read -rp "Cookie value: " cookie_value

if [[ -z "$cookie_value" ]]; then
    echo "ERROR: No value provided. Aborting." >&2
    exit 1
fi

# Format as proper Cookie header value
full_cookie="_ollama_session=${cookie_value}"

echo ""
echo "Copying to Pi (${PI_HOST})..."

# Create temp file locally, scp it, then ssh to move and restart
echo "$full_cookie" > /tmp/ollama-cookie.tmp

scp /tmp/ollama-cookie.tmp "${PI_HOST}:/tmp/ollama-cookie.tmp"

ssh "${PI_HOST}" "
    mkdir -p ~/.config/ollama-widget &&
    mv /tmp/ollama-cookie.tmp '${PI_PATH}' &&
    chmod 600 '${PI_PATH}' &&
    chown \$(whoami):\$(whoami) '${PI_PATH}' 2>/dev/null || true &&
    echo 'Cookie saved to ${PI_PATH} (mode 600).' &&
    if systemctl is-active --quiet ollama-widget-scraper 2>/dev/null; then
        echo 'Restarting ollama-widget-scraper...'
        sudo systemctl restart ollama-widget-scraper
        echo 'Done. Scraper restarted.'
    else
        echo 'Note: ollama-widget-scraper service not running (expected during prototype).'
        echo 'Start it with: python3 pi/scraper/scraper.py  (prototype one-shot)'
        echo 'Or: sudo systemctl start ollama-widget-scraper  (production)'
    fi
"

rm -f /tmp/ollama-cookie.tmp

echo ""
echo "================================="
echo "Sync complete."
