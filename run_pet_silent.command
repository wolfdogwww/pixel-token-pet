#!/bin/bash
# Pixel Token Pet — macOS silent launcher (no Terminal window stays open)
# Double-click this file in Finder to start the pet silently.

cd "$(dirname "$0")"

if ! command -v python3 &>/dev/null; then
    osascript -e 'display alert "Python 3 not found" message "Install from https://python.org  or run:  brew install python3"'
    exit 1
fi

if ! python3 -c "import pystray, PIL" 2>/dev/null; then
    python3 -m pip install --quiet pystray pillow
fi

# Launch in background so Terminal closes immediately
nohup python3 pixel_token_pet.py >/dev/null 2>&1 &

# Close the Terminal window that opened this script
sleep 0.3
osascript -e 'tell application "Terminal" to close (every window whose frontmost is true)' 2>/dev/null
