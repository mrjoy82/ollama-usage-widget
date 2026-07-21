#!/usr/bin/env python3
"""
Prototype scraper for Ollama usage widget.
Fetches https://ollama.com/settings, extracts session + weekly usage,
writes JSON cache.
"""

import json
import os
import re
import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

COOKIE_PATH = Path.home() / ".config" / "ollama-widget" / "cookie.txt"
CACHE_PATH = Path.home() / ".local" / "share" / "ollama-widget" / "usage.json"
SETTINGS_URL = "https://ollama.com/settings"
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)
TIMEOUT = 10  # seconds for HTTP fetch

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_cookie():
    if not COOKIE_PATH.exists():
        return None
    return COOKIE_PATH.read_text().strip()

def write_cache(data):
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps(data, indent=2))

def parse_percent(text):
    if not text:
        return None
    m = re.search(r"([\d.]+)\s*%", text)
    return float(m.group(1)) if m else None

def parse_resets(text):
    if not text:
        return None
    m = re.search(r"resets?\s+in\s+(.+?)\.?\s*$", text, re.IGNORECASE)
    return m.group(1).strip() if m else text.strip() or None

def fetch_and_parse(cookie):
    headers = {
        "Cookie": cookie,
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml",
    }
    resp = requests.get(SETTINGS_URL, headers=headers, timeout=TIMEOUT)

    # Ollama redirects to /signin when cookie is bad
    if 300 <= resp.status_code < 400:
        raise RuntimeError(f"Cookie expired or invalid (redirect, status {resp.status_code})")
    if not resp.ok:
        raise RuntimeError(f"HTTP {resp.status_code} from ollama.com")

    soup = BeautifulSoup(resp.text, "html.parser")

    # Anchor on data-usage-meter (validated selector from RESEARCH.md)
    meters = soup.find_all(attrs={"data-usage-meter": True})
    if not meters:
        raise RuntimeError("No [data-usage-meter] elements found — page structure changed?")

    blocks = []
    for meter in meters:
        # Label + percent in previous sibling div.flex → spans
        label_row = meter.find_previous_sibling("div", class_="flex")
        label = None
        percent_text = None
        if label_row:
            spans = label_row.find_all("span")
            if spans:
                label = spans[0].get_text(strip=True)
                percent_text = spans[-1].get_text(strip=True)

        # Reset string in next sibling (class local-time or any element with "Resets in")
        reset_text = None
        nxt = meter.find_next_sibling()
        guard = 0
        while nxt and guard < 4:
            txt = nxt.get_text(strip=True)
            if re.search(r"resets?\s+in", txt, re.IGNORECASE):
                reset_text = txt
                break
            nxt = nxt.find_next_sibling()
            guard += 1

        blocks.append({
            "label": label,
            "percent_text": percent_text,
            "reset_text": reset_text,
        })

    # Classify by label (session vs weekly), fallback to position
    session = None
    weekly = None
    for b in blocks:
        lbl = (b["label"] or "").lower()
        if "session" in lbl and not session:
            session = b
        elif "week" in lbl and not weekly:
            weekly = b
    if not session and blocks:
        session = blocks[0]
    if not weekly and len(blocks) > 1:
        weekly = blocks[1]

    def to_usage(b):
        if not b:
            return None
        return {
            "percent": parse_percent(b["percent_text"]),
            "label": b["percent_text"] or None,
            "resets_in": parse_resets(b["reset_text"]),
        }

    return {
        "session": to_usage(session),
        "weekly": to_usage(weekly),
    }

def run_scraper():
    cookie = load_cookie()
    if not cookie:
        print("ERROR: No cookie found at", COOKIE_PATH, file=sys.stderr)
        write_cache({
            "status": "error",
            "error": "cookie_missing",
            "message": f"Cookie file not found at {COOKIE_PATH}",
            "updated_at": None,
        })
        return

    try:
        parsed = fetch_and_parse(cookie)
        data = {
            "status": "ok",
            "session_pct": parsed["session"]["percent"] if parsed["session"] else None,
            "weekly_pct": parsed["weekly"]["percent"] if parsed["weekly"] else None,
            "session_resets_in": parsed["session"]["resets_in"] if parsed["session"] else None,
            "weekly_resets_in": parsed["weekly"]["resets_in"] if parsed["weekly"] else None,
            "updated_at": None,  # filled below
        }
    except Exception as e:
        print("ERROR:", e, file=sys.stderr)
        data = {
            "status": "error",
            "error": type(e).__name__,
            "message": str(e),
            "updated_at": None,
        }

    data["updated_at"] = __import__("datetime").datetime.now().isoformat()
    write_cache(data)
    print(json.dumps(data, indent=2))

if __name__ == "__main__":
    run_scraper()
