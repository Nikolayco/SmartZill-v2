#!/bin/bash

cd "$(dirname "$0")"
fuser -k 7777/tcp

echo -ne "\033]0;Nikolayco_SmartZill_Terminal\007"
sleep 0.5

if command -v xdotool &> /dev/null; then
    xdotool search --name "Nikolayco_SmartZill_Terminal" windowminimize
elif command -v wmctrl &> /dev/null; then
    wmctrl -r "Nikolayco_SmartZill_Terminal" -b add,hidden
fi
echo -ne "\033[2t"

echo "Starting NikolayCo SmartZill..."

# Check for required system packages
MISSING_PKGS=""

if ! command -v vlc &> /dev/null; then
    MISSING_PKGS="$MISSING_PKGS vlc"
fi

if ! dpkg -s python3-venv &> /dev/null; then
     # ensuring venv is present (common issue on Debian/Ubuntu)
     if ! python3 -c "import venv" &> /dev/null; then
        MISSING_PKGS="$MISSING_PKGS python3-venv"
     fi
fi

if ! command -v ffmpeg &> /dev/null; then
    MISSING_PKGS="$MISSING_PKGS ffmpeg"
fi

if [ ! -z "$MISSING_PKGS" ]; then
    echo "ERROR: Missing required system packages:$MISSING_PKGS"
    echo "Please install them with: sudo apt install$MISSING_PKGS"
    echo "Press Enter to exit..."
    read
    exit 1
fi


VENV_DIR=".venv"

if [ ! -d "$VENV_DIR" ]; then
    echo "Creating Python Virtual Environment ($VENV_DIR)..."
    python3 -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"
pip install -r requirements.txt > /dev/null 2>&1
export PYTHONUNBUFFERED=1

python smartzill.py &
APP_PID=$!

echo "Waiting for System to initialize..."
MAX_RETRIES=30
COUNT=0
while ! curl -s http://localhost:7777 > /dev/null; do
    sleep 1
    COUNT=$((COUNT+1))
    if [ $COUNT -ge $MAX_RETRIES ]; then
        echo "System failed to start in time!"
        exit 1
    fi
    echo -n "."
done
echo "System Ready!"
sleep 2
echo "App PID: $APP_PID"

wait $APP_PID
