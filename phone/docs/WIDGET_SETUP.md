# KWGT Widget Setup Guide

## Prerequisites
- KWGT Kustom Widget Maker installed from Play Store
- KWGT Pro Key (required for external data via `$wg()`)
- Your Pi API running at `http://100.126.198.43:7582`

## Step 1: Add a Blank KWGT Widget to Home Screen
1. Long-press empty space on Pixel 8 Pro home screen
2. Tap **Widgets**
3. Find **KWGT** → select a **1x1** blank widget
4. Drag it to your desired spot
5. Tap the blank widget to open the KWGT editor

## Step 2: Create the Layout

In the KWGT editor, add these elements in order:

### Element 1: Background (optional but recommended)
- Add → Shape → Rectangle
- Size: Fill parent (match widget bounds)
- Color: transparent or Material You surface color
- Corner radius: 16dp (matches Material You cards)
- This sits at the back (send to back)

### Element 2: Session Percentage (large, top)
- Add → Text
- Text formula:
  ```
  $if($wg(http://100.126.198.43:7582/usage, .status)$="ok", $wg(http://100.126.198.43:7582/usage, .session_pct)$+"%", "N/A")$
  ```
- Font: your preferred bold font, size ~36sp
- Color: Material You accent color (or white/black depending on wallpaper)
- Position: Top center of widget
- Gravity: center

### Element 3: Weekly Percentage (small, bottom)
- Add → Text
- Text formula:
  ```
  $if($wg(http://100.126.198.43:7582/usage, .status)$="ok", "W: "+$wg(http://100.126.198.43:7582/usage, .weekly_pct)$+"%", "")$
  ```
- Font: same family, size ~14sp
- Color: slightly muted (e.g., 80% opacity of primary text)
- Position: Bottom center of widget
- Gravity: center

### Element 4: Reset Timer (optional, very small)
- Add → Text
- Text formula:
  ```
  $if($wg(http://100.126.198.43:7582/usage, .status)$="ok", $wg(http://100.126.198.43:7582/usage, .session_resets_in)$, "")$
  ```
- Font: size ~10sp
- Color: muted (60% opacity)
- Position: Below session %, above weekly %

### Element 5: Border (for error state indication)
- Add → Shape → Rectangle
- Size: Fill parent, slightly smaller than background (2dp inset on each side)
- Fill: transparent
- Stroke/Border: 2dp
- Stroke color formula:
  ```
  $if($wg(http://100.126.198.43:7582/usage, .status)$!="ok", #ff4444, #00000000)$
  ```
  (This shows red border when status is not "ok")
- Corner radius: 16dp
- Send to back (behind text, above background)

**Note on initialization:** When the widget first loads and has no data yet, `$wg()` returns empty. The formulas above will show "N/A" until the first successful fetch. If you want a different initial placeholder, wrap the formulas in additional `$if` checks for empty strings.

## Step 3: Configure Refresh Interval
1. In KWGT editor, tap the **Global** (gear) icon at top right
2. Go to **Widget Preferences** or **General**
3. Set **Auto Update** to 10 minutes (600 seconds)
   - If KWGT doesn't offer 10 min exactly, use the closest option (typically 5, 10, or 15 min)

## Step 4: Tap-to-Refresh (Optional but Recommended)
1. Add a small refresh icon (Add → FontIcon or a small text element with "↻")
2. Position: Top-right corner or next to the session percentage
3. Set **Touch → Open Link**
4. URL: `http://100.126.198.43:7582/usage?refresh=1`
5. Or set Touch → Launch Shortcut → URL (depending on KWGT version)

**Alternative:** Make the entire widget area tappable for refresh:
- Select the background shape
- Touch → Open Link → `http://100.126.198.43:7582/usage?refresh=1`

## Step 5: Save and Export
1. Tap **Save** (disk icon) in KWGT editor
2. Name it: "Ollama Usage"
3. Back on home screen, the widget should appear
4. **Export for backup:**
   - In KWGT editor, tap the menu (⋮) → **Export** → **Export Preset**
   - Save as `ollama-usage.kwgt`
   - Move the file to this repo: `phone/ollama-usage.kwgt`

## KWGT Formula Reference

### Full session formula with all edge cases:
```
$if(
  $wg(http://100.126.198.43:7582/usage, .status)$="ok",
  $wg(http://100.126.198.43:7582/usage, .session_pct)$+"%",
  if(
    $wg(http://100.126.198.43:7582/usage, .error)$="cookie_missing" | 
    $wg(http://100.126.198.43:7582/usage, .error)$="scraper_auth_failed",
    "N/A",
    "OFFLINE"
  )
)$
```

**Note:** The exact formula syntax depends on your KWGT version. The formulas above use `$if(condition, true, false)` which is standard in KWGT. If your version uses different syntax (e.g., `if()` or conditional operators), adjust accordingly.

## Troubleshooting

### Widget shows "N/A" constantly
- Check Pi API: `curl http://100.126.198.43:7582/usage` from another device
- Verify cookie is valid on Pi
- Check Tailscale connection on phone

### Widget is blank / empty
- `$wg()` may be returning null before first fetch
- Add a fallback: `$if($wg(...)$="", "...", $wg(...)$)`

### Widget doesn't update automatically
- Android Doze may be throttling KWGT
- In Pixel Settings → Apps → KWGT → Battery → set to "Unrestricted"

### Border doesn't show error color
- The border color formula checks `.status` — verify the API returns `"status": "ok"`
- The border is transparent (#00000000) when status is ok

## Material You Styling Tips
- Use rounded corners (16dp) to match Pixel 8 Pro's card style
- Text color: `$mu(color, accent)` for dynamic Material You theming (if supported)
- Background: semi-transparent Material You surface variant
- For a cleaner look, omit the reset timer and just show the two percentages
