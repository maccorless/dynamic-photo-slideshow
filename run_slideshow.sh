#!/bin/bash
# Wrapper script to run the pygame-based slideshow

# Check if virtual environment exists and use it, otherwise use system Python
if [ -d "slideshow_env" ]; then
    echo "Using virtual environment..."
    PYTHON_CMD="./slideshow_env/bin/python"
    
    # Install pygame dependencies in virtual env if needed
    if ! $PYTHON_CMD -c "import pygame" 2>/dev/null; then
        echo "Installing pygame dependencies in virtual environment..."
        $PYTHON_CMD -m pip install pygame>=2.5.0 pyvidplayer2>=0.9.18
    fi
else
    echo "Using system Python..."
    # Set the path to use system Python
    export PATH="/usr/bin:$PATH"
    PYTHON_CMD="/usr/bin/python3"
    
    # Install dependencies for system Python if needed
    if ! $PYTHON_CMD -c "import osxphotos" 2>/dev/null; then
        echo "Installing dependencies for system Python..."
        $PYTHON_CMD -m pip install --user --upgrade pip
        $PYTHON_CMD -m pip install --user osxphotos>=0.60.0 Pillow>=9.0.0 requests>=2.28.0 pygame>=2.5.0 pyvidplayer2>=0.9.18
    fi
    
    # Check for pygame specifically
    if ! $PYTHON_CMD -c "import pygame" 2>/dev/null; then
        echo "Installing pygame for system Python..."
        $PYTHON_CMD -m pip install --user pygame>=2.5.0 pyvidplayer2>=0.9.18
    fi
fi

# Run the slideshow
echo "Starting Dynamic Photo Slideshow (Pygame Version)..."
echo "Make sure you have created the 'photoframe' album in Photos and added some photos."
echo ""
$PYTHON_CMD main_pygame.py
