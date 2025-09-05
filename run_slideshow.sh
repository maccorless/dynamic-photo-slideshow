#!/bin/bash
# Wrapper script to run the slideshow with system Python (which has tkinter)

# Set the path to use system Python
export PATH="/usr/bin:$PATH"

# Install dependencies for system Python if needed
if ! /usr/bin/python3 -c "import osxphotos" 2>/dev/null; then
    echo "Installing dependencies for system Python..."
    /usr/bin/python3 -m pip install --user --upgrade pip
    /usr/bin/python3 -m pip install --user osxphotos>=0.60.0 Pillow>=9.0.0 requests>=2.28.0
fi

# Run the slideshow
echo "Starting Dynamic Photo Slideshow..."
echo "Make sure you have created the 'photoframe' album in Photos and added some photos."
echo ""
/usr/bin/python3 main.py
