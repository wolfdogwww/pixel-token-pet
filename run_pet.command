#!/bin/bash
# Pixel Token Pet — macOS launcher
# Double-click this file in Finder to start the pet.

cd "$(dirname "$0")"

# ── Check Python 3 ──────────────────────────────────────────────────────────
if ! command -v python3 &>/dev/null; then
    osascript -e 'display alert "Python 3 not found" message "Install from https://python.org  or run:  brew install python3"'
    exit 1
fi

# ── Install optional tray dependencies (pystray + Pillow) if missing ────────
if ! python3 -c "import pystray, PIL" 2>/dev/null; then
    echo "Installing pystray and Pillow for system-tray support…"
    python3 -m pip install --quiet pystray pillow
fi

# ── Launch ───────────────────────────────────────────────────────────────────
python3 pixel_token_pet.py
