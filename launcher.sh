#!/bin/bash
# Photo Slideshow Launcher
# Auto-detects installation directory and virtual environment

set -e  # Exit on error

# Get the directory where this script lives
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "🎬 Starting Photo Slideshow..."
echo "📁 Installation: $SCRIPT_DIR"

# Find a working virtual environment python binary
# Venvs break if the project directory is moved, so verify the python binary actually works
find_working_venv() {
    for VENV_DIR in "$SCRIPT_DIR/venv" "$SCRIPT_DIR/slideshow_env"; do
        if [ -x "$VENV_DIR/bin/python3" ] && "$VENV_DIR/bin/python3" -c "import sys" 2>/dev/null; then
            echo "$VENV_DIR/bin/python3"
            return 0
        fi
    done
    return 1
}

PYTHON=$(find_working_venv) && {
    echo "🐍 Using virtual environment: $PYTHON"
} || {
    # No working venv found — try to rebuild it
    echo "⚠️  Virtual environment is missing or broken. Rebuilding..."
    python3 -m venv "$SCRIPT_DIR/venv" --clear 2>/dev/null || {
        rm -rf "$SCRIPT_DIR/venv"
        python3 -m venv "$SCRIPT_DIR/venv"
    }
    "$SCRIPT_DIR/venv/bin/pip" install -r "$SCRIPT_DIR/requirements.txt" --quiet
    PYTHON="$SCRIPT_DIR/venv/bin/python3"
    echo "✅ Virtual environment rebuilt at $SCRIPT_DIR/venv"
}

# Change to script directory
cd "$SCRIPT_DIR"

# Check if main_pygame.py exists
if [ ! -f "main_pygame.py" ]; then
    echo "❌ Error: main_pygame.py not found in $SCRIPT_DIR"
    echo "   Please run install.sh first"
    exit 1
fi

# Check for config file
if [ ! -f ~/.photo_slideshow_config.json ]; then
    echo "⚙️  Config file not found, creating from template..."
    if [ -f "photo_slideshow_config.json" ]; then
        cp photo_slideshow_config.json ~/.photo_slideshow_config.json
        echo "✅ Config created at ~/.photo_slideshow_config.json"
        echo "📝 Edit config before running: nano ~/.photo_slideshow_config.json"
        echo ""
        read -p "Press Enter to continue or Ctrl+C to exit and edit config..."
    else
        echo "⚠️  Warning: Template config not found, proceeding anyway..."
    fi
fi

# Run the slideshow with any passed arguments
echo "🚀 Launching slideshow..."
echo ""
$PYTHON main_pygame.py "$@"

# Capture exit code
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    echo ""
    echo "❌ Slideshow exited with error code: $EXIT_CODE"
    echo "📋 Check logs in current directory for details"
fi

exit $EXIT_CODE
