#!/bin/bash
# Spotify TUI Launcher Script
# This script activates the virtual environment and runs spotifytui

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PATH="$SCRIPT_DIR/spotifytui_env"

# Check if virtual environment exists
if [ ! -d "$VENV_PATH" ]; then
    echo "❌ Virtual environment not found at $VENV_PATH"
    echo "Please run setup first from the project directory."
    exit 1
fi

# Activate virtual environment and run spotifytui
source "$VENV_PATH/bin/activate"
"$VENV_PATH/bin/spotifytui"
