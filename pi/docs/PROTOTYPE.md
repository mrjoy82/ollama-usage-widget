# Prototype: End-to-End Usage Widget

## Files

- `pi/scraper/scraper.py` — Fetches Ollama settings, parses usage, writes JSON cache
- `pi/api/app.py` — Flask API serving cached usage data
- `pi/scraper/requirements.txt` — Python dependencies for scraper
- `pi/api/requirements.txt` — Python dependencies for API

## Quick Start

### 1. Install dependencies (both sides use same venv for prototype)

```bash
cd pi
python3 -m venv .venv
source .venv/bin/activate
pip install -r scraper/requirements.txt -r api/requirements.txt
```

### 2. Set up cookie

Log in to https://ollama.com/settings in your browser. Copy the full `_ollama_session` cookie value. Paste it into:

```bash
mkdir -p ~/.config/ollama-widget
echo "_ollama_session=YOUR_COOKIE_VALUE_HERE" > ~/.config/ollama-widget/cookie.txt
chmod 600 ~/.config/ollama-widget/cookie.txt
```

### 3. Run scraper (standalone test)

```bash
cd pi/scraper
python3 scraper.py
```

Expected output on success:
```json
{
  "status": "ok",
  "session_pct": 45.8,
  "weekly_pct": 45.8,
  "session_resets_in": "4 hours",
  "weekly_resets_in": "3 days",
  "updated_at": "2026-07-21T..."
}
```

Expected on auth failure:
```json
{
  "status": "error",
  "error": "RuntimeError",
  "message": "Cookie expired or invalid (redirect, status 303)",
  "updated_at": "..."
}
```

### 4. Run API (in another terminal)

```bash
cd pi/api
python3 app.py
```

The API listens on `http://0.0.0.0:7582`.

### 5. Test from the Pi itself

```bash
curl http://localhost:7582/health
curl http://localhost:7582/usage
curl "http://localhost:7582/usage?refresh=1"
```

### 6. Test from your phone

Ensure your phone is on Tailscale. Then:

```
http://100.126.198.43:7582/usage
```

Or use a browser on the phone to visit that URL.

## Go/No-Go Criteria

| Check | Pass Criteria |
|-------|--------------|
| Scraper fetches Ollama | HTTP 200, JSON cache written |
| Parser extracts both percentages | `session_pct` and `weekly_pct` are numbers |
| API serves JSON | `GET /usage` returns valid JSON |
| Phone reaches Pi | Browser/curl from phone gets response |
| Manual refresh works | `?refresh=1` triggers live fetch |
| Error states clear | Bad cookie → 503 with clear error message |

If all pass → proceed to #6 (production scraper), #7 (production API), #8 (widget).
If any fail → revisit architecture (#1) or research (#2).
