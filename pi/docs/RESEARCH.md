# Research: Ollama Settings Page DOM and Cookie Requirements

## Source
Primary source: [OllamaDash](https://github.com/Brinven/OllamaDash) by Brinven
— a working, production Home Assistant integration that scrapes the same page.
Secondary source: Home Assistant community post confirming the approach.

## Authentication

### Mechanism
Standard HTTP session cookie. The settings page returns **HTTP 303** redirect
to `https://signin.ollama.com` when no valid cookie is present.

### Cookie Format
A raw Cookie header string, e.g.:
```
_ollama_session=abc123...; other_cookie=xyz...
```
Stored as a single string value. No API key alternative exists.

### Expiration
Unknown TTL. OllamaDash logs: "Cookie expired or not authenticated (redirected
to login)" when a 3xx is received. In practice, users report re-copying every
few days to weeks.

### No API Key Path
Confirmed by GitHub issue #15663 (closed as duplicate of #12532). No official
API for usage/quota exists as of July 2026.

## Page Structure (from validated parser)

### URL
`https://ollama.com/settings`

### User-Agent Used by Working Scraper
```
Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36
```

### Key DOM Elements

#### 1. Usage Meter (primary anchor)
```html
<div data-usage-meter>
  <!-- Per-model segments inside -->
  <button data-usage-segment data-model="gemma4:31b" data-requests="369"></button>
</div>
```

#### 2. Label + Percent (previous sibling)
```html
<div class="flex">
  <span>Session Usage</span>
  <span>45.8% used</span>
</div>
```

#### 3. Reset Timer (next sibling)
```html
<div class="local-time">Resets in 4 hours.</div>
```

### Data Extracted

| Field | Selector / Method | Example |
|-------|-------------------|---------|
| `session.percent` | `[data-usage-meter]` → prev sibling span text, regex `([\d.]+)\s*%` | `45.8` |
| `weekly.percent` | Same, second meter | `45.8` |
| `session.resets_in` | Next sibling text, regex `resets?\s+in\s+(.+?)\.?\s*$` | `4 hours` |
| `weekly.resets_in` | Same | `3 days` |
| `model_note` | `[data-usage-segment]` `data-model` + `data-requests` | `gemma4:31b, 369 requests` |

### Parsing Robustness
The parser anchors on `[data-usage-meter]` and walks siblings dynamically.
This is resilient to Tailwind class churn because it does not rely on specific
class names. The `data-usage-meter` and `data-usage-segment` attributes are
custom data attributes that are stable semantic markers.

### Metrics Available
1. **Session Usage** — percentage of session limit consumed
2. **Weekly Usage** — percentage of weekly limit consumed
3. **Reset Timers** — human-readable "resets in X"
4. **Model Breakdown** — per-model request counts inside the usage bar

## Anti-Bot / Rate Limiting

| Concern | Finding |
|---------|---------|
| CAPTCHA | None detected on settings page |
| 2FA | None detected |
| Rate limits | Unknown; OllamaDash defaults to 120s cache, suggesting no hard limit |
| Bot detection | Standard fetch with Chrome UA succeeds |
| Cloudflare | None observed |

## HTML Sample (reconstructed from parser logic)

```html
<!-- Session block -->
<div class="flex">
  <span>Session Usage</span>
  <span>45.8% used</span>
</div>
<div data-usage-meter>
  <button data-usage-segment data-model="gemma4:31b" data-requests="369"></button>
  <button data-usage-segment data-model="qwen3:30b" data-requests="120"></button>
</div>
<div class="local-time">Resets in 4 hours.</div>

<!-- Weekly block -->
<div class="flex">
  <span>Weekly Usage</span>
  <span>45.8% used</span>
</div>
<div data-usage-meter>
  <button data-usage-segment data-model="gemma4:31b" data-requests="369"></button>
</div>
<div class="local-time">Resets in 3 days.</div>
```

## Cookie Acquisition Steps (for user)

1. Log in to https://ollama.com in a desktop browser
2. Navigate to https://ollama.com/settings
3. Open DevTools → Application/Storage → Cookies → ollama.com
4. Copy the full `_ollama_session` cookie value (or entire Cookie header)
5. Paste into `/opt/ollama-widget/cookie.txt` on the Pi
6. Restart scraper: `sudo systemctl restart ollama-widget-scraper`

## Implications for Our Architecture

1. **Both session and weekly** percentages are available. The widget can show
   whichever the user prefers, or both.
2. **Reset timer** is useful context — "45% used, resets in 4 hours" is more
   meaningful than just "45%".
3. **Model breakdown** could be exposed in a detailed view, but the widget
   should probably stay minimal (percentage + reset timer).
4. **Cookie refresh** is manual. We should make the update path as simple as
   editing one file and running one command.
5. **Parser is validated** — we can port the OllamaDash parsing logic to Python
   with `BeautifulSoup4` using the same selectors.
