#!/bin/bash
# Photo Slideshow Uninstall Script
# Removes old installation from /opt/slideshow and optionally the new one

set -e  # Exit on error

echo "========================================"
echo "Photo Slideshow - Uninstall"
echo "========================================"
echo ""

# Function to remove directory with confirmation
remove_directory() {
    local dir=$1
    local description=$2
    
    if [ -d "$dir" ]; then
        echo "📁 Found: $description"
        echo "   Location: $dir"
        
        if [ -n "$(ls -A $dir 2>/dev/null)" ]; then
            SIZE=$(du -sh "$dir" 2>/dev/null | cut -f1 || echo "unknown")
            echo "   Size: $SIZE"
        fi
        
        read -p "   Remove this directory? (yes/no): " -r
        if [[ $REPLY =~ ^[Yy]es$ ]]; then
            if [[ "$dir" == /Applications/* ]] || [[ "$dir" == /opt/* ]]; then
                sudo rm -rf "$dir"
            else
                rm -rf "$dir"
            fi
            echo "   ✅ Removed"
            return 0
        else
            echo "   ⏭️  Skipped"
            return 1
        fi
    else
        echo "ℹ️  Not found: $description ($dir)"
        return 1
    fi
    echo ""
}

# Remove old installation at /opt/slideshow
echo "Checking for old installation..."
echo ""
remove_directory "/opt/slideshow" "Old installation (/opt/slideshow)"
echo ""

# Ask about new installation
echo "Checking for current installation..."
echo ""
if remove_directory "/Applications/PhotoSlideshow" "Current installation (/Applications/PhotoSlideshow)"; then
    REMOVED_NEW=true
else
    REMOVED_NEW=false
fi
echo ""

# Ask about desktop shortcut
echo "Checking for desktop shortcut..."
echo ""
remove_directory "$HOME/Desktop/PhotoSlideshow.command" "Desktop shortcut"
echo ""

# Ask about config and cache
echo "========================================"
echo "User Data"
echo "========================================"
echo ""
echo "The following user data can also be removed:"
echo ""

# Config file
if [ -f ~/.photo_slideshow_config.json ]; then
    echo "📄 Configuration file"
    echo "   Location: ~/.photo_slideshow_config.json"
    read -p "   Remove config file? (yes/no): " -r
    if [[ $REPLY =~ ^[Yy]es$ ]]; then
        rm ~/.photo_slideshow_config.json
        echo "   ✅ Removed"
    else
        echo "   ⏭️  Kept (you can manually delete later)"
    fi
else
    echo "ℹ️  No config file found"
fi
echo ""

# Video cache
if [ -d ~/.photo_slideshow_cache ]; then
    CACHE_SIZE=$(du -sh ~/.photo_slideshow_cache 2>/dev/null | cut -f1 || echo "unknown")
    echo "📦 Video cache"
    echo "   Location: ~/.photo_slideshow_cache"
    echo "   Size: $CACHE_SIZE"
    read -p "   Remove cache? (yes/no): " -r
    if [[ $REPLY =~ ^[Yy]es$ ]]; then
        rm -rf ~/.photo_slideshow_cache
        echo "   ✅ Removed"
    else
        echo "   ⏭️  Kept (you can manually delete later)"
    fi
else
    echo "ℹ️  No cache directory found"
fi
echo ""

echo "========================================"
echo "Uninstall Complete"
echo "========================================"
echo ""

if [ "$REMOVED_NEW" = true ]; then
    echo "✅ Photo Slideshow has been completely removed"
    echo ""
    echo "To reinstall:"
    echo "  curl -O https://raw.githubusercontent.com/maccorless/dynamic-photo-slideshow/photo-video-voice/install.sh"
    echo "  chmod +x install.sh"
    echo "  ./install.sh"
else
    echo "✅ Old installation removed (if it existed)"
    echo ""
    echo "Current installation remains at:"
    echo "  /Applications/PhotoSlideshow"
fi
echo ""
