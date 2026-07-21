# Architecture: Ollama Usage Widget

## Overview
A Raspberry Pi 4/5 scrapes Ollama Cloud usage from https://ollama.com/settings
every 10 minutes and serves it via a lightweight HTTP API. An Android phone (Pixel 8
Pro) displays the value in a KWGT home screen widget, polling the Pi over Tailscale.

## Components

### 1. Pi Scraper Service (`pi/scraper/`)
- Python script using `requests` + `BeautifulSoup4`
- Authenticates to ollama.com with session cookie from local file
- Extracts usage percentage from DOM using validated CSS selector
- Writes result to JSON cache: `/var/lib/ollama-widget/usage.json`
- Runs on 10-minute interval via `systemd timer` or Python `sched`
- Logs to systemd journal (`journalctl -u ollama-widget-scraper`)

### 2. Pi API Service (`pi/api/`)
- Minimal Flask app, single endpoint: `GET /usage`
- Serves cached JSON from scraper
- Binds to `0.0.0.0:PORT` (Tailscale interface preferred)
- CORS enabled for KWGT browser fetcher
- HTTP basic auth or Tailscale IP allowlist (decision pending #4)
- systemd service for auto-start

### 3. Phone Widget (`phone/`)
- KWGT Kustom Widget Maker
- `$wg()` formula polls Pi API every 10 minutes
- Displays usage percentage + optional Material You progress bar
- Error state: shows last known value with stale indicator or "N/A"

## Network Topology

```
                    +------------------+          +------------------+
                    |  ollama.com      |          |   Android Phone   |
                    |  /settings       |          |  (Pixel 8 Pro)    |
                    +--------+---------+          +--------+---------+
                             |                             |
                    HTTPS    |                    HTTP     |
                    (cookie) |                    (poll)    |
                             v                             v
                    +--------+---------+          +--------+---------+
                    |   Pi Scraper     |          |   KWGT Widget    |
                    |   (python)       |          |   $wg(formula)   |
                    +--------+---------+          +--------+---------+
                             |                             |
                    write    |                    read     |
                    JSON     |                    /usage   |
                             v                             v
                    +--------+---------+          +--------+---------+
                    |  /var/lib/       |<---------|   Pi Flask API   |
                    |  usage.json      |  HTTP    |   (python)       |
                    +------------------+          +--------+---------+
                                                           |
                                                  0.0.0.0:PORT (Tailscale)
                                                           |
                                                           v
                                                  +--------+---------+
                                                  |   100.x.x.x      |
                                                  |   (Tailscale IP)  |
                                                  +------------------+
```

## Data Flow
1. Scraper fetches https://ollama.com/settings (authenticated)
2. Scraper parses HTML, extracts usage percentage
3. Scraper writes `{"usage_pct": 47, "updated_at": "...", "status": "ok"}` to cache
4. Flask API reads cache file, serves on `GET /usage`
5. KWGT widget polls `GET /usage` every 10 min
6. Widget renders text + optional progress bar

## Decisions (from #1)

| Item | Decision | Rationale |
|------|----------|-----------|
| Port | 7582 | Unassigned in IANA, unlikely to conflict. Easy to type. |
| Cookie storage | `/opt/ollama-widget/cookie.txt`, mode 600 | Standard path, restricted permissions |
| Cache file | `/var/lib/ollama-widget/usage.json` | FHS-compliant for runtime data |
| Pi bind address | `0.0.0.0` (all interfaces) | Tailscale IP is one of them; ACLs enforce access |
| Auth for API | HTTP Basic Auth (optional, default off) | Tailscale already provides mTLS-like security; basic auth as defense-in-depth |
| Scraper schedule | systemd timer, 10 min OnCalendar | More reliable than cron for service-like semantics |
| Parsing library | BeautifulSoup4 | DOM-based, more resilient than regex to minor HTML changes |
| Phone polling | KWGT native `$wg()` | No Tasker needed; built-in HTTP + JSON parsing |

## API Schema

### GET /usage

**Success (200):**
```json
{
  "usage_pct": 47,
  "updated_at": "2026-07-21T20:00:00+08:00",
  "status": "ok",
  "source": "ollama.com/settings"
}
```

**Error - auth failed on scraper (503):**
```json
{
  "status": "error",
  "error": "scraper_auth_failed",
  "message": "Cookie may be expired",
  "updated_at": "2026-07-21T20:00:00+08:00"
}
```

**Error - cache missing (503):**
```json
{
  "status": "error",
  "error": "cache_missing",
  "message": "Scraper has not produced a cache file yet"
}
```

## File Layout (repo)
```
ollama-usage-widget/
├── README.md
├── .gitignore
├── pi/
│   ├── scraper/
│   │   ├── scraper.py
│   │   ├── requirements.txt
│   │   └── ollama-widget-scraper.service
│   ├── api/
│   │   ├── app.py
│   │   ├── requirements.txt
│   │   └── ollama-widget-api.service
│   └── docs/
│       ├── ARCHITECTURE.md          (this file)
│       ├── COOKIE_UPDATE.md          (how to refresh cookie)
│       └── TROUBLESHOOTING.md
└── phone/
    └── docs/
        └── WIDGET_SETUP.md
```

## Tailscale Reachability
- Pi Tailscale IP: `100.126.198.43`
- Phone accesses: `http://100.126.198.43:7582/usage`
- No port forwarding, no firewall rules needed — Tailscale ACLs handle access

## Security Notes
- Cookie file must be `chmod 600`
- API can be restricted to Tailscale IPs in Flask if desired
- No secrets in repo; cookie and auth config are local Pi files only
