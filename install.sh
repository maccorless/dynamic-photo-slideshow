#!/bin/bash
# Photo Slideshow Installation Script
# Performs clean installation to /Applications/PhotoSlideshow

set -e  # Exit on error

INSTALL_DIR="/Applications/PhotoSlideshow"
REPO_URL="https://github.com/maccorless/dynamic-photo-slideshow.git"
BRANCH="photo-video-voice"
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

# Check for Python 3
echo "🐍 Checking for Python 3..."

# Try python3.13 first, then python3
PYTHON_CMD=""

# Check for python3.13 first, then python3.12, then python3.11
if command -v python3.13 &> /dev/null; then
    PYTHON_CMD="python3.13"
    PYTHON_VERSION=$(python3.13 --version | cut -d' ' -f2)
    echo "   Found python3.13: $PYTHON_VERSION"
elif [ -x "/opt/homebrew/bin/python3.13" ]; then
    PYTHON_CMD="/opt/homebrew/bin/python3.13"
    PYTHON_VERSION=$(/opt/homebrew/bin/python3.13 --version | cut -d' ' -f2)
    echo "   Found python3.13 in Homebrew: $PYTHON_VERSION"
elif [ -x "/usr/local/bin/python3.13" ]; then
    PYTHON_CMD="/usr/local/bin/python3.13"
    PYTHON_VERSION=$(/usr/local/bin/python3.13 --version | cut -d' ' -f2)
    echo "   Found python3.13 in /usr/local: $PYTHON_VERSION"
elif command -v python3.12 &> /dev/null; then
    PYTHON_CMD="python3.12"
    PYTHON_VERSION=$(python3.12 --version | cut -d' ' -f2)
    echo "   Found python3.12: $PYTHON_VERSION"
elif [ -x "/opt/homebrew/bin/python3.12" ]; then
    PYTHON_CMD="/opt/homebrew/bin/python3.12"
    PYTHON_VERSION=$(/opt/homebrew/bin/python3.12 --version | cut -d' ' -f2)
    echo "   Found python3.12 in Homebrew: $PYTHON_VERSION"
elif [ -x "/usr/local/bin/python3.12" ]; then
    PYTHON_CMD="/usr/local/bin/python3.12"
    PYTHON_VERSION=$(/usr/local/bin/python3.12 --version | cut -d' ' -f2)
    echo "   Found python3.12 in /usr/local: $PYTHON_VERSION"
elif command -v python3.11 &> /dev/null; then
    PYTHON_CMD="python3.11"
    PYTHON_VERSION=$(python3.11 --version | cut -d' ' -f2)
    echo "   Found python3.11: $PYTHON_VERSION"
elif [ -x "/opt/homebrew/bin/python3.11" ]; then
    PYTHON_CMD="/opt/homebrew/bin/python3.11"
    PYTHON_VERSION=$(/opt/homebrew/bin/python3.11 --version | cut -d' ' -f2)
    echo "   Found python3.11 in Homebrew: $PYTHON_VERSION"
elif [ -x "/usr/local/bin/python3.11" ]; then
    PYTHON_CMD="/usr/local/bin/python3.11"
    PYTHON_VERSION=$(/usr/local/bin/python3.11 --version | cut -d' ' -f2)
    echo "   Found python3.11 in /usr/local: $PYTHON_VERSION"
elif command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    echo "   Found python3: $PYTHON_VERSION"
    
    if version_ge "$PYTHON_VERSION" "$REQUIRED_PYTHON_VERSION"; then
        PYTHON_CMD="python3"
    else
        echo "   ❌ Python $PYTHON_VERSION is too old (need $REQUIRED_PYTHON_VERSION+)"
        echo ""
        echo "   Please install Python 3.11+:"
        echo "   • Via Homebrew: brew install python@3.13"
        echo "   • Or download from: https://www.python.org/downloads/"
        exit 1
    fi
fi

if [ -z "$PYTHON_CMD" ]; then
    echo "   ❌ Python 3.11+ not found"
    echo ""
    echo "Please install Python 3.11+:"
    echo "   • Via Homebrew: brew install python@3.13"
    echo "   • Or download from: https://www.python.org/downloads/"
    exit 1
fi

echo "   ✅ Using $PYTHON_CMD (version $PYTHON_VERSION)"

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
