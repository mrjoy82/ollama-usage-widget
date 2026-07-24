#!/usr/bin/env python3
"""
Build a minimal KWGT preset (.kwgt file) for the Ollama usage widget.
KWGT presets are ZIP files containing preset.json and optional assets.
"""

import json
import zipfile
import os

# KWGT preset structure
preset = {
    "title": "Ollama Usage",
    "author": "ABIS HK / Hermes Agent",
    "description": "Display Ollama Cloud session and weekly usage from Pi API",
    "width": 1,
    "height": 1,
    "items": [
        {
            "type": "Shape",
            "width": 120,
            "height": 120,
            "posX": 0,
            "posY": 0,
            "paintStyle": "FILL",
            "color": "#E8EAED",
            "cornerRadius": 16,
            "paintStroke": False,
            "strokeWidth": 0,
            "paintShadow": False
        },
        {
            "type": "Text",
            "text": '$wg(http://100.126.198.43:7582/usage, .session_pct)$%',
            "width": 120,
            "height": 60,
            "posX": 0,
            "posY": 10,
            "fontSize": 32,
            "fontStyle": "BOLD",
            "fontColor": "#202124",
            "gravity": "CENTER",
            "paintShadow": False
        },
        {
            "type": "Text",
            "text": 'W: $wg(http://100.126.198.43:7582/usage, .weekly_pct)$%',
            "width": 120,
            "height": 30,
            "posX": 0,
            "posY": 70,
            "fontSize": 14,
            "fontStyle": "NORMAL",
            "fontColor": "#5F6368",
            "gravity": "CENTER",
            "paintShadow": False
        },
        {
            "type": "Shape",
            "width": 116,
            "height": 116,
            "posX": 2,
            "posY": 2,
            "paintStyle": "STROKE",
            "color": "$if($wg(http://100.126.198.43:7582/usage, .status)$!=ok, #ff4444, #00000000)$",
            "cornerRadius": 14,
            "paintStroke": True,
            "strokeWidth": 2,
            "paintShadow": False
        }
    ],
    "globals": [],
    "touch": {
        "type": "OPEN_LINK",
        "url": "http://100.126.198.43:7582/usage?refresh=1"
    }
}

# Build ZIP
output_path = "phone/ollama-usage.kwgt"
with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
    zf.writestr("preset.json", json.dumps(preset, indent=2))

print(f"Created: {output_path}")
print(f"Size: {os.path.getsize(output_path)} bytes")

# Verify
with zipfile.ZipFile(output_path, 'r') as zf:
    print("Contents:", zf.namelist())
    print("\npreset.json preview:")
    print(zf.read("preset.json").decode('utf-8')[:500])
