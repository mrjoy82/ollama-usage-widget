#!/usr/bin/env bash
# macbook-sync-cookie.sh
# Run this on your MacBook when the Ollama cookie expires.
# It copies the cookie from your clipboard (pbpaste) to the Pi,
# sets permissions, and restarts the scraper.
#
# Prerequisites:
#   - 'TAgent' SSH alias works from this MacBook
#   - You are logged into Tailscale
#   - You have already copied the _ollama_session cookie value to your clipboard
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
echo "This script reads the cookie value from your macOS clipboard."
echo ""
echo "BEFORE RUNNING THIS SCRIPT, you must copy the cookie from Chrome:"
echo ""
echo "  1. Open Chrome and go to: https://ollama.com/settings"
echo "  2. Make sure you are LOGGED IN (the page should show your usage)"
echo "  3. Press F12 (or right-click anywhere → Inspect)"
echo "  4. Click the 'Application' tab at the top of DevTools"
echo "  5. In the left sidebar, expand: Cookies → https://ollama.com"
echo "  6. Look for the row with Name: _ollama_session"
echo "  7. Double-click the VALUE column — it is a long random string"
echo "  8. Press Cmd+C to copy it to your clipboard"
echo ""
echo "Then run this script. It will paste from your clipboard automatically."
echo ""

# macOS has pbpaste; if not available, fallback to manual temp file
if command -v pbpaste &>/dev/null; then
    echo "Reading from clipboard..."
    cookie_value=$(pbpaste | tr -d '\n\r')
else
    echo "pbpaste not found. Falling back to manual temp file."
    tmpfile=$(mktemp)
    echo "A temp file has been created at: $tmpfile"
    echo "Open it in your editor, paste the cookie value, save and close."
    read -rp "Press Enter to open ${EDITOR:-nano}..."
    ${EDITOR:-nano} "$tmpfile"
    cookie_value=$(cat "$tmpfile" | tr -d '\n\r')
    rm -f "$tmpfile"
fi

if [[ -z "$cookie_value" ]]; then
    echo "ERROR: Clipboard is empty or temp file is empty. Aborting." >&2
    exit 1
fi

# Format as proper Cookie header value
full_cookie="_ollama_session=${cookie_value}"

echo ""
echo "Cookie value length: ${#cookie_value} characters"
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
