#!/bin/bash
# Photo Slideshow Launcher
# Auto-detects installation directory and virtual environment

set -e  # Exit on error

# Get the directory where this script lives
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "🎬 Starting Photo Slideshow..."
echo "📁 Installation: $SCRIPT_DIR"

# Check if virtual environment exists and activate it
if [ -f "$SCRIPT_DIR/venv/bin/activate" ]; then
    echo "🐍 Activating virtual environment..."
    source "$SCRIPT_DIR/venv/bin/activate"
else
    echo "⚠️  Warning: Virtual environment not found at $SCRIPT_DIR/venv"
    echo "   Using system Python instead"
fi

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
python main_pygame.py "$@"

# Capture exit code
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    echo ""
    echo "❌ Slideshow exited with error code: $EXIT_CODE"
    echo "📋 Check logs in current directory for details"
fi

exit $EXIT_CODE
