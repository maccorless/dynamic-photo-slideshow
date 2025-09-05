#!/bin/bash
# Script to clean up Python installations and use only Homebrew Python 3.13.7

echo "🧹 Cleaning up Python installations..."

# 1. Remove pyenv from shell configuration
echo "Removing pyenv from shell configuration..."
sed -i '' '/pyenv/d' ~/.zshrc 2>/dev/null || true

# 2. Set Homebrew Python as default
echo "Setting up Homebrew Python as default..."
echo 'export PATH="/opt/homebrew/bin:$PATH"' >> ~/.zshrc

# 3. Remove pyenv version file
rm -f ~/.pyenv/version

# 4. Reload shell configuration
echo "Reloading shell configuration..."
source ~/.zshrc

echo "✅ Python cleanup complete!"
echo ""
echo "🔍 Verifying setup..."
/opt/homebrew/bin/python3 --version
echo "Python location: $(which python3)"
echo ""
echo "🚀 Next steps:"
echo "1. Open a new terminal window"
echo "2. Run: python3 --version (should show 3.13.7)"
echo "3. Install slideshow dependencies: python3 -m pip install --user -r requirements.txt"
echo "4. Run the slideshow: python3 main.py"
