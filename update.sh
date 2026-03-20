#!/bin/bash
# Photo Slideshow Update Script
# Updates code from GitHub while preserving config and cache

set -e  # Exit on error

# Get the directory where this script lives
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BRANCH="main"

echo "========================================"
echo "Photo Slideshow - Update"
echo "========================================"
echo ""
echo "Installation: $SCRIPT_DIR"
echo ""

# Verify we're in a git repository
if [ ! -d "$SCRIPT_DIR/.git" ]; then
    echo "❌ Error: Not a git repository"
    echo "   This doesn't appear to be a valid installation"
    echo "   Please run install.sh for a fresh installation"
    exit 1
fi

# Change to script directory
cd "$SCRIPT_DIR"

# Check for uncommitted changes
if ! git diff-index --quiet HEAD -- 2>/dev/null; then
    echo "⚠️  Warning: You have uncommitted changes in the installation directory"
    echo ""
    git status --short
    echo ""
    read -p "Stash changes and continue? (yes/no): " -r
    if [[ $REPLY =~ ^[Yy]es$ ]]; then
        git stash push -m "Auto-stash before update $(date +%Y-%m-%d_%H:%M:%S)"
        echo "   ✅ Changes stashed"
    else
        echo "Update cancelled"
        exit 0
    fi
fi

# Fetch latest changes
echo "📥 Fetching latest changes from GitHub..."
git fetch origin "$BRANCH"

# Show what will be updated
echo ""
echo "📋 Changes to be applied:"
git log --oneline HEAD..origin/"$BRANCH" | head -10
echo ""

read -p "Continue with update? (yes/no): " -r
if [[ ! $REPLY =~ ^[Yy]es$ ]]; then
    echo "Update cancelled"
    exit 0
fi

# Backup current log
echo ""
echo "📋 Backing up current log..."
if [ -f "stderr.log" ]; then
    cp stderr.log stderr.log.bak
    rm stderr.log
    echo "   ✅ Log backed up to stderr.log.bak"
fi

# Pull latest changes
echo ""
echo "⬇️  Pulling latest changes..."
git pull origin "$BRANCH"
echo "   ✅ Code updated"

# Activate virtual environment
if [ -f "venv/bin/activate" ]; then
    echo ""
    echo "🐍 Activating virtual environment..."
    source venv/bin/activate
    
    # Update dependencies
    echo ""
    echo "📦 Updating Python dependencies..."
    if [ -f "requirements.txt" ]; then
        pip install --upgrade pip
        pip install -r requirements.txt
        echo "   ✅ Dependencies updated"
    else
        echo "   ⚠️  Warning: requirements.txt not found"
    fi
else
    echo ""
    echo "⚠️  Warning: Virtual environment not found"
    echo "   Dependencies not updated"
fi

# Check config for new options
echo ""
echo "⚙️  Checking configuration..."
if [ -f "photo_slideshow_config.json" ] && [ -f ~/.photo_slideshow_config.json ]; then
    # Count keys in template vs user config
    TEMPLATE_KEYS=$(python3 -c "import json; print(len(json.load(open('photo_slideshow_config.json'))))" 2>/dev/null || echo "0")
    USER_KEYS=$(python3 -c "import json; print(len(json.load(open('$HOME/.photo_slideshow_config.json'))))" 2>/dev/null || echo "0")
    
    if [ "$TEMPLATE_KEYS" -gt "$USER_KEYS" ]; then
        echo "   ℹ️  New configuration options available"
        echo "   Template: $TEMPLATE_KEYS options"
        echo "   Your config: $USER_KEYS options"
        echo ""
        echo "   To see new options:"
        echo "   diff ~/.photo_slideshow_config.json photo_slideshow_config.json"
        echo ""
        echo "   Your existing config has been preserved"
    else
        echo "   ✅ Configuration is up to date"
    fi
else
    echo "   ✅ Configuration preserved"
fi

# Video cache is preserved (not cleaned on update)
if [ -d ~/.photo_slideshow_cache/videos ]; then
    CACHE_SIZE=$(du -sh ~/.photo_slideshow_cache/videos | cut -f1)
    echo "   ℹ️  Video cache preserved ($CACHE_SIZE)"
fi

echo ""
echo "========================================="
echo "✅ Update Complete!"
echo "========================================="
echo ""
echo "Changes applied: $(git log --oneline HEAD~1..HEAD | wc -l) commit(s)"
echo ""
echo "To run the slideshow:"
echo "  ./launcher.sh"
echo ""
echo "To view what changed:"
echo "  git log --oneline -10"
echo ""
