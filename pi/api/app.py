#!/usr/bin/env python3
"""
Prototype Flask API for Ollama usage widget.
Serves cached usage data from the scraper.
"""

import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timezone

from flask import Flask, jsonify
from flask_cors import CORS

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

CACHE_PATH = Path.home() / ".local" / "share" / "ollama-widget" / "usage.json"
SCRAPER_SCRIPT = Path(__file__).parent.parent / "scraper" / "scraper.py"
PORT = 7582
STALE_MINUTES = 30

app = Flask(__name__)
CORS(app)  # Allow KWGT browser fetcher

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_cache():
    if not CACHE_PATH.exists():
        return None
    try:
        return json.loads(CACHE_PATH.read_text())
    except (json.JSONDecodeError, OSError):
        return None

def is_stale(cache):
    if not cache or not cache.get("updated_at"):
        return True
    try:
        updated = datetime.fromisoformat(cache["updated_at"])
        age = datetime.now(timezone.utc) - updated.replace(tzinfo=timezone.utc)
        return age.total_seconds() > (STALE_MINUTES * 60)
    except Exception:
        return True

def run_scraper():
    """Run the scraper synchronously. Returns (success: bool, output: str)."""
    try:
        result = subprocess.run(
            [sys.executable, str(SCRAPER_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=15,
        )
        return result.returncode == 0, result.stdout
    except subprocess.TimeoutExpired:
        return False, "Scraper timed out"
    except Exception as e:
        return False, str(e)

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/health")
def health():
    return jsonify({"status": "ok", "port": PORT})

@app.route("/usage")
def usage():
    refresh = __import__("flask").request.args.get("refresh", "0") == "1"
    cache = load_cache()

    if refresh:
        ok, _ = run_scraper()
        if ok:
            cache = load_cache()

    if not cache:
        return jsonify({
            "status": "error",
            "error": "cache_missing",
            "message": "Scraper has not produced a cache file yet",
        }), 503

    # Build response
    resp = {
        "session_pct": cache.get("session_pct"),
        "weekly_pct": cache.get("weekly_pct"),
        "session_resets_in": cache.get("session_resets_in"),
        "weekly_resets_in": cache.get("weekly_resets_in"),
        "updated_at": cache.get("updated_at"),
        "status": cache.get("status", "ok"),
    }

    if cache.get("status") != "ok":
        resp["error"] = cache.get("error")
        resp["message"] = cache.get("message")
        return jsonify(resp), 503

    if is_stale(cache):
        resp["stale"] = True
        resp["source"] = "stale_cache"

    return jsonify(resp)

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print(f"[prototype-api] Starting on http://0.0.0.0:{PORT}")
    print(f"[prototype-api] Cache: {CACHE_PATH}")
    print(f"[prototype-api] Scraper: {SCRAPER_SCRIPT}")
    app.run(host="0.0.0.0", port=PORT, debug=False)
