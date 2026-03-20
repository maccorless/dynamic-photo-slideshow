#!/bin/bash
# Photo Slideshow Patch Script
# Pulls latest Python code from main. Does NOT touch settings, cache, or venv.

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "Photo Slideshow - Patch"
echo ""

if [ ! -d ".git" ]; then
    echo "❌ Not a git repository. Run install.sh for a fresh install."
    exit 1
fi

echo "📥 Pulling latest code from main..."
git fetch origin main

CHANGES=$(git log --oneline HEAD..origin/main)
if [ -z "$CHANGES" ]; then
    echo "✅ Already up to date."
    exit 0
fi

echo ""
echo "Changes:"
echo "$CHANGES"
echo ""

git merge --ff-only origin/main
echo ""
echo "✅ Patch applied. Restart the slideshow to pick up changes."
