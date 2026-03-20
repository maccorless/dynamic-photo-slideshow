#!/bin/bash
# Photo Slideshow Installation Script
# Performs clean installation to /Applications/PhotoSlideshow

set -e  # Exit on error

INSTALL_DIR="/Applications/PhotoSlideshow"
REPO_URL="https://github.com/maccorless/dynamic-photo-slideshow.git"
BRANCH="main"
REQUIRED_PYTHON_VERSION="3.11"

echo "========================================"
echo "Photo Slideshow - Clean Installation"
echo "========================================"
echo ""

# Check if running with sudo (we don't want that for /Applications)
if [ "$EUID" -eq 0 ]; then 
    echo "❌ Error: Do not run this script with sudo"
    echo "   The script will request admin password when needed"
    exit 1
fi

# Function to compare version numbers
version_ge() {
    # Returns 0 (true) if $1 >= $2
    printf '%s\n%s\n' "$2" "$1" | sort -V -C
}

# Check for Python 3.11+
echo "🐍 Checking for Python 3..."

# Locate Homebrew prefix regardless of whether brew is in PATH
# (scripts launched from .command files on the Desktop may not inherit the user's PATH)
BREW_PREFIX=""
if [ -x "/opt/homebrew/bin/brew" ]; then
    BREW_PREFIX="/opt/homebrew"        # Apple Silicon
elif [ -x "/usr/local/bin/brew" ]; then
    BREW_PREFIX="/usr/local"           # Intel
fi

# find_python: returns the path to the best available Python 3.11+
# Checks Homebrew explicit paths first so it works even when brew isn't in PATH,
# then falls back to versioned commands in PATH.
find_python() {
    local versions=("3.13" "3.12" "3.11")
    for ver in "${versions[@]}"; do
        # Homebrew framework path (most explicit — works even if brew not in PATH)
        if [ -n "$BREW_PREFIX" ] && [ -x "$BREW_PREFIX/opt/python@$ver/bin/python$ver" ]; then
            echo "$BREW_PREFIX/opt/python@$ver/bin/python$ver"; return 0
        fi
        # Homebrew bin symlink
        if [ -n "$BREW_PREFIX" ] && [ -x "$BREW_PREFIX/bin/python$ver" ]; then
            echo "$BREW_PREFIX/bin/python$ver"; return 0
        fi
        # Versioned command in PATH
        if command -v "python$ver" &>/dev/null; then
            echo "python$ver"; return 0
        fi
    done
    return 1
}

PYTHON_CMD=$(find_python || true)

# If nothing found, try to install via Homebrew automatically
if [ -z "$PYTHON_CMD" ]; then
    echo "   ❌ Python 3.11+ not found"
    echo ""
    BREW_CMD="${BREW_PREFIX:+$BREW_PREFIX/bin/brew}"
    BREW_CMD="${BREW_CMD:-$(command -v brew 2>/dev/null || true)}"
    if [ -n "$BREW_CMD" ] && [ -x "$BREW_CMD" ]; then
        echo "   Homebrew found. Installing Python 3.13 automatically..."
        "$BREW_CMD" install python@3.13
        PYTHON_CMD=$(find_python || true)
    fi
fi

if [ -z "$PYTHON_CMD" ]; then
    echo "   ❌ Python 3.11+ not found and could not be installed automatically"
    echo ""
    echo "   Install Python 3.13 manually, then re-run this script:"
    echo "   • Via Homebrew: brew install python@3.13"
    echo "   • Or download from: https://www.python.org/downloads/"
    exit 1
fi

PYTHON_VERSION=$("$PYTHON_CMD" --version 2>&1 | cut -d' ' -f2)
echo "   ✅ Using $PYTHON_CMD ($PYTHON_VERSION)"

# Check for git
echo "📦 Checking for git..."
if ! command -v git &> /dev/null; then
    echo "   ❌ git not found"
    echo ""
    echo "Please install git:"
    echo "   xcode-select --install"
    exit 1
else
    echo "   ✅ git is installed"
fi

# Check for ffmpeg/ffprobe (required for video playback)
echo "🎬 Checking for ffmpeg..."
if ! command -v ffprobe &> /dev/null; then
    echo "   ⚠️  ffmpeg not found (required for video playback)"
    echo ""
    echo "Install ffmpeg via Homebrew:"
    echo "   brew install ffmpeg"
    echo ""
    read -p "Continue without ffmpeg? Videos will not play. (yes/no): " -r
    if [[ ! $REPLY =~ ^[Yy]es$ ]]; then
        echo "Installation cancelled"
        echo "Please install ffmpeg and run this script again"
        exit 0
    fi
    echo "   ⚠️  Continuing without ffmpeg - videos will not work"
else
    FFMPEG_VERSION=$(ffmpeg -version | head -n1 | cut -d' ' -f3)
    echo "   ✅ ffmpeg is installed (version $FFMPEG_VERSION)"
fi

# Warn if old installation exists
if [ -d "/opt/slideshow" ]; then
    echo ""
    echo "⚠️  WARNING: Old installation detected at /opt/slideshow"
    echo "   This will NOT be removed automatically"
    echo "   After successful installation, run: ./uninstall.sh"
    echo ""
    read -p "Continue with new installation? (yes/no): " -r
    if [[ ! $REPLY =~ ^[Yy]es$ ]]; then
        echo "Installation cancelled"
        exit 0
    fi
fi

# Check if installation directory exists
if [ -d "$INSTALL_DIR" ]; then
    echo ""
    echo "⚠️  Installation directory already exists: $INSTALL_DIR"
    read -p "Remove existing installation and reinstall? (yes/no): " -r
    if [[ $REPLY =~ ^[Yy]es$ ]]; then
        echo "🗑️  Removing existing installation..."
        sudo rm -rf "$INSTALL_DIR"
    else
        echo "Installation cancelled"
        exit 0
    fi
fi

# Create installation directory
echo ""
echo "📁 Creating installation directory..."
sudo mkdir -p "$INSTALL_DIR"
sudo chown $(whoami):staff "$INSTALL_DIR"
echo "   ✅ Created $INSTALL_DIR"

# Clone repository
echo ""
echo "📥 Cloning repository from GitHub..."
git clone -b "$BRANCH" "$REPO_URL" "$INSTALL_DIR"
echo "   ✅ Repository cloned"

# Change to installation directory
cd "$INSTALL_DIR"

# Create virtual environment
echo ""
echo "🐍 Creating virtual environment..."
$PYTHON_CMD -m venv venv
echo "   ✅ Virtual environment created"

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo ""
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo ""
echo "📦 Installing Python dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    echo "   ✅ Dependencies installed"
else
    echo "   ⚠️  Warning: requirements.txt not found"
fi

# Setup configuration
echo ""
echo "⚙️  Setting up configuration..."
if [ ! -f ~/.photo_slideshow_config.json ]; then
    if [ -f "photo_slideshow_config.json" ]; then
        cp photo_slideshow_config.json ~/.photo_slideshow_config.json
        echo "   ✅ Config created at ~/.photo_slideshow_config.json"
    else
        echo "   ⚠️  Warning: Template config not found"
    fi
else
    echo "   ℹ️  Config already exists at ~/.photo_slideshow_config.json"
    echo "   Keeping existing configuration"
fi

# Clean video cache (fresh install)
echo ""
echo "🗑️  Cleaning video cache (fresh install)..."
if [ -d ~/.photo_slideshow_cache/videos ]; then
    rm -rf ~/.photo_slideshow_cache/videos
    echo "   ✅ Video cache cleaned"
fi

# Clean logs but backup last one
echo ""
echo "📋 Managing logs..."
if [ -f "$INSTALL_DIR/stderr.log" ]; then
    cp "$INSTALL_DIR/stderr.log" "$INSTALL_DIR/stderr.log.bak"
    rm "$INSTALL_DIR/stderr.log"
    echo "   ✅ Previous log backed up to stderr.log.bak"
fi

# Create desktop shortcut
echo ""
echo "🖥️  Creating desktop shortcut..."
DESKTOP_SHORTCUT="$HOME/Desktop/PhotoSlideshow.command"
cat > "$DESKTOP_SHORTCUT" << 'EOF'
#!/bin/bash
cd "/Applications/PhotoSlideshow" && ./launcher.sh
EOF
chmod +x "$DESKTOP_SHORTCUT"
echo "   ✅ Desktop shortcut created"

# Make launcher executable
chmod +x launcher.sh

echo ""
echo "========================================="
echo "✅ Installation Complete!"
echo "========================================="
echo ""
echo "Installation location: $INSTALL_DIR"
echo "Configuration file:    ~/.photo_slideshow_config.json"
echo ""
echo "To run the slideshow:"
echo "  • Double-click 'PhotoSlideshow' on Desktop"
echo "  • Or run: cd $INSTALL_DIR && ./launcher.sh"
echo ""
echo "To customize settings:"
echo "  nano ~/.photo_slideshow_config.json"
echo ""
echo "To update in the future:"
echo "  cd $INSTALL_DIR && ./update.sh"
echo ""
if [ -d "/opt/slideshow" ]; then
    echo "⚠️  Don't forget to remove old installation:"
    echo "  cd $INSTALL_DIR && ./uninstall.sh"
    echo ""
fi
