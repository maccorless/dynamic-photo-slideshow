#!/bin/bash
# Complete deployment script for Dynamic Photo Slideshow
# This script clones/pulls the latest code and sets up the config

set -e  # Exit on any error

echo "🚀 Dynamic Photo Slideshow - Full Deployment Script"
echo "=================================================="

# Check if we're in an existing repo or need to clone
if [ -d ".git" ]; then
    echo "📁 Existing repository detected. Pulling latest changes..."
    git checkout photo-video-voice
    git pull origin photo-video-voice
    echo "✅ Repository updated successfully"
else
    echo "❌ Error: Not in a git repository"
    echo ""
    echo "Please run one of these commands first:"
    echo ""
    echo "Option 1 - Clone the repository:"
    echo "  git clone -b photo-video-voice https://github.com/maccorless/dynamic-photo-slideshow.git"
    echo "  cd dynamic-photo-slideshow"
    echo "  ./deploy.sh"
    echo ""
    echo "Option 2 - If you already have the files, initialize git:"
    echo "  git init"
    echo "  git remote add origin https://github.com/maccorless/dynamic-photo-slideshow.git"
    echo "  git fetch origin photo-video-voice"
    echo "  git checkout photo-video-voice"
    echo ""
    exit 1
fi

# Set up config file
if [ ! -f ~/.photo_slideshow_config.json ]; then
    echo "⚙️  Setting up configuration file..."
    cp photo_slideshow_config.json ~/.photo_slideshow_config.json
    echo "✅ Config file created at ~/.photo_slideshow_config.json"
    echo "📝 Edit the config file to customize settings:"
    echo "   nano ~/.photo_slideshow_config.json"
else
    echo "⚙️  Config file already exists at ~/.photo_slideshow_config.json"
    echo "💡 To update with latest defaults, run:"
    echo "   cp photo_slideshow_config.json ~/.photo_slideshow_config.json"
fi

# Install dependencies (optional - uncomment if needed)
# echo "📦 Installing dependencies..."
# pip install -r requirements.txt

echo ""
echo "🎉 Deployment complete!"
echo ""
echo "Next steps:"
echo "1. Edit ~/.photo_slideshow_config.json to customize settings"
echo "2. Run: python main_pygame.py"
echo ""
echo "For help, see README.md and DEPLOYMENT.md"
