# Grilling Session: Locked Decisions

**Session date:** 2026-07-21
**Scope:** Phase 1 — Pi-backed Android widget for Ollama Cloud usage (session % + weekly %)
**Griller:** Hermes Agent (kimi-k2.6:cloud)
**Grillee:** Matthieu (ABIS HK Founder/CEO)

---

## Architecture Reference

All decisions below are consistent with `ARCHITECTURE.md` and `RESEARCH.md` in this repo.

---

## 1. Authentication & Session

### 1.1 Cookie Expiration Strategy
**Decision:** Explicit error state (Option B)
- When cookie expires, scraper detects 303 redirect, logs clear error
- API returns 503 with `{"status": "error", "error": "scraper_auth_failed"}`
- Widget shows "N/A" immediately — no stale data, no silent failure
- Grace period: none; auth failure is treated as hard error

### 1.2 Cookie Refresh Workflow
**Decision:** SSH manual update with convenience script (Option A + B)
- Path: `~/.config/ollama-widget/cookie.txt`
- Mode: `600`, owner: `matthieu`
- Script: `scripts/update-cookie.sh` — prompts for cookie, writes with proper permissions, restarts scraper
- No admin endpoint, no Termux dependency, no phone-side auth
- Revisit if SSH-from-phone becomes burdensome

### 1.3 Scraper User
**Decision:** Run as `matthieu` (Option C)
- Cookie lives in XDG-compliant path under home directory
- No dedicated system user (Pi is personal device)
- No root required for service execution

---

## 2. Reliability

### 2.1 Pi Reboot Recovery
**Decision:** Warm start with immediate scraper run (Option B)
- systemd timer triggers `OnBootSec=10s` — scraper runs immediately after boot
- No waiting for 10-minute interval
- API serves data within ~30 seconds of boot

### 2.2 Manual Refresh from Widget
**Decision:** Hybrid synchronous with timeout (Option C)
- `GET /usage?refresh=1` attempts live fetch from ollama.com
- Timeout: 3 seconds
- If live fetch succeeds → fresh data immediately
- If live fetch fails → fall back to cached value with `stale: true`
- No error state on timeout; user always sees a number

### 2.3 Ollama.com Downtime
**Decision:** Serve stale cache with degraded flag (Option B)
- API continues serving last known value
- Response includes `"source": "stale_cache"` and `"last_success"` timestamp
- Widget visual indicator: gray text / red border (depending on error type)

### 2.4 Ollama Layout Change
**Decision:** Explicit error, no fallback parser, no HTML snapshot (Option B)
- Parser breaks → scraper writes error to cache → API 503 → widget "N/A"
- No secondary parsing strategy (complexity not justified for Phase 1)
- No raw HTML snapshot (user delegates log inspection to agent)
- When widget goes red, user asks agent to inspect `journalctl` for root cause

### 2.5 Phone Cannot Reach Pi
**Decision:** Distinct offline state (Option C)
- KWGT `$wg()` timeout → null/empty result
- Widget formula handles null: displays "OFFLINE" in gray
- Tap-to-refresh available even when offline (will retry connection)

### 2.6 Android Doze / Overnight
**Decision:** Accepted (Option A)
- No special handling for Doze throttling
- Widget refreshes when phone wakes/unlocks
- Stale overnight data is acceptable for a glance-at widget
- Tap-to-refresh provides on-demand freshness

### 2.7 First Boot / No Cache Yet
**Decision:** Neutral placeholder (Option A)
- Before first successful fetch: widget shows "..." or "—"
- No timestamp subtext (deferred to Phase 2 if needed)
- User sees placeholder for < 1 minute under normal conditions

---

## 3. Visual / Widget Layout

### 3.1 Widget Size
**Decision:** 1x1 (single grid cell on Pixel 8 Pro)
- Session %: large text on top
- Weekly %: smaller text below
- Evaluate 2x1 after prototype if 1x1 feels cramped

### 3.2 Error Display
**Decision:** Hard errors = single text; stale = gray numbers (Option A + B)
- Auth fail / unreachable / parse fail: widget shows single centered text ("N/A" or "OFFLINE")
- Stale cache: both numbers visible but grayed out
- Border color encodes state:
  - **No border** = fresh data
  - **Gray border** = initializing / no data yet
  - **Red border** = any error condition

### 3.3 Color Scheme
**Decision:** Minimal semantic colors (user-refined from standard options)
- No Material You dynamic palette dependency
- Colors hardcoded in KWGT formula; configurable if requested later

---

## 4. Security

### 4.1 API Access Control
**Decision:** No HTTP auth on API (Option A)
- Tailscale wireguard + ACLs provide network-level authentication
- API is read-only, no sensitive data exposed (cookie never leaves Pi)
- If Tailscale network shared with others in future, revisit basic auth

---

## 5. Data & Logging

### 5.1 Phase 1 Data Scope
**Decision:** Two numbers only — session_pct + weekly_pct
- API returns both: `{"session_pct": 45.8, "weekly_pct": 45.8, ...}`
- Widget displays session prominently, weekly as secondary
- API schema leaves door open for Phase 2 (models array can be added without breaking change)

### 5.2 Historical Data / Mission Control Integration
**Decision:** Deferred to Phase 2
- Phase 1 scraper writes single JSON cache file only
- JSONL time-series and model breakdowns planned for Phase 2
- Pi data directory (`~/.local/share/ollama-widget/`) reserved for future history storage

### 5.3 Logging Strategy
**Decision:** journald INFO level (agent's call)
- Canonical log: `journalctl -u ollama-widget-scraper`, `journalctl -u ollama-widget-api`
- Log level: `INFO` during Phase 1 (every fetch attempt visible for debugging)
- Downgrade to `WARNING` after stability proven (weeks of operation)
- No redundant log files on disk
- `/health` endpoint stays simple; `/status` deferred to Phase 2 if needed

---

## 6. Phase 2 Door (Open)

The following are NOT built in Phase 1, but the architecture does not prevent them:

| Feature | Phase 1 Status | Phase 2 Path |
|---------|---------------|--------------|
| Per-model breakdown | Not scraped | Add `models: [...]` to API schema, update scraper |
| Historical time-series | Not stored | Add JSONL file in `~/.local/share/ollama-widget/` |
| Mission Control integration | Not connected | Pi exposes history endpoint or pushes to MC webhook |
| Full-screen detail view | Not built | Browser opens `GET /details` served by Pi Flask |
| Timestamp subtext | Not shown | Add to KWGT formula if user requests |
| 2x1 widget size | Not used | Resize in KWGT editor if 1x1 is too small |

---

## 7. Decisions by Ticket

| Ticket | Status | Key Decisions Locked |
|--------|--------|---------------------|
| #1 map | CLOSED | Port 7582, Tailscale IP 100.126.198.43, systemd services, BeautifulSoup4 |
| #2 research | CLOSED | Cookie auth, `[data-usage-meter]` selector, session + weekly metrics |
| #4 grilling | THIS FILE | All failure modes, visual states, auth strategy, logging, scope |
| #5 prototype | NEXT | Build throwaway scraper + Flask + phone test (4hr timebox) |
| #6 scraper | OPEN | Production scraper with systemd timer, JSON cache, error handling |
| #7 API | OPEN | Flask API, CORS, GET /usage, GET /usage?refresh=1, error states |
| #8 widget | OPEN | KWGT 1x1, session/weekly layout, tap-to-refresh, color borders |

---

*End of grilling session. All branches resolved. Proceed to prototype (#5).*
