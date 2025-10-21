# Deployment Guide

Complete deployment system for Photo Slideshow on runtime machines.

## Quick Start

### Fresh Installation

On the runtime machine:

```bash
# Download and run the installer
curl -O https://raw.githubusercontent.com/maccorless/dynamic-photo-slideshow/photo-video-voice/install.sh
chmod +x install.sh
./install.sh
```

The installer will:
- ✅ Check for Python 3.9+ (install if needed)
- ✅ Clone repository to `/Applications/PhotoSlideshow`
- ✅ Create virtual environment
- ✅ Install all dependencies
- ✅ Setup configuration file
- ✅ Create desktop shortcut
- ✅ Clean video cache and logs

### Update Existing Installation

```bash
cd /Applications/PhotoSlideshow
./update.sh
```

The updater will:
- ✅ Pull latest code from GitHub
- ✅ Update Python dependencies
- ✅ Preserve your configuration
- ✅ Preserve video cache
- ✅ Backup current log to `stderr.log.bak`

### Remove Old Installation

If you have the old installation at `/opt/slideshow`:

```bash
cd /Applications/PhotoSlideshow
./uninstall.sh
```

## Running the Slideshow

### Option 1: Desktop Shortcut
Double-click **PhotoSlideshow** on your Desktop

### Option 2: Command Line
```bash
cd /Applications/PhotoSlideshow
./launcher.sh
```

## File Locations

| Item | Location | Preserved on Update? |
|------|----------|---------------------|
| Application | `/Applications/PhotoSlideshow/` | ✅ Updated |
| Configuration | `~/.photo_slideshow_config.json` | ✅ Yes |
| Video Cache | `~/.photo_slideshow_cache/videos/` | ✅ Yes |
| Current Log | `/Applications/PhotoSlideshow/stderr.log` | ❌ Backed up |
| Previous Log | `/Applications/PhotoSlideshow/stderr.log.bak` | ⚠️ Overwritten |

## Configuration

### Edit Settings
```bash
nano ~/.photo_slideshow_config.json
```

### Copy Config to Another Machine
```bash
# From development machine
scp ~/.photo_slideshow_config.json username@runtime-machine:~

# On runtime machine (will be auto-detected on next run)
# Or manually place it:
mv ~/photo_slideshow_config.json ~/.photo_slideshow_config.json
```

### Reset to Defaults
```bash
cp /Applications/PhotoSlideshow/photo_slideshow_config.json ~/.photo_slideshow_config.json
```

## Troubleshooting

### Python Not Found
Install Python 3.9 or newer:
```bash
# Using Homebrew
brew install python@3.11

# Or download from python.org
open https://www.python.org/downloads/
```

### Git Not Found
```bash
xcode-select --install
```

### Permission Errors
The installer will request admin password when needed. Do NOT run with `sudo`.

### Old Installation Conflicts
If you have the old `/opt/slideshow` installation:
1. Run the new installer first
2. Then run `./uninstall.sh` to remove the old one

### Virtual Environment Issues
```bash
cd /Applications/PhotoSlideshow
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Desktop Shortcut Not Working
Recreate it:
```bash
cat > ~/Desktop/PhotoSlideshow.command << 'EOF'
#!/bin/bash
cd "/Applications/PhotoSlideshow" && ./launcher.sh
EOF
chmod +x ~/Desktop/PhotoSlideshow.command
```

## Advanced Usage

### Custom Install Location
Edit `install.sh` and change:
```bash
INSTALL_DIR="/Applications/PhotoSlideshow"
```

### Development Mode
To work on the code while running:
```bash
cd /Applications/PhotoSlideshow
source venv/bin/activate
python main_pygame.py
```

### View Logs
```bash
# Current session
tail -f /Applications/PhotoSlideshow/stderr.log

# Previous session
cat /Applications/PhotoSlideshow/stderr.log.bak
```

### Check for Updates Manually
```bash
cd /Applications/PhotoSlideshow
git fetch origin photo-video-voice
git log HEAD..origin/photo-video-voice
```

## Complete Uninstall

To remove everything:
```bash
cd /Applications/PhotoSlideshow
./uninstall.sh
```

This will prompt you to remove:
- Old installation (`/opt/slideshow`)
- Current installation (`/Applications/PhotoSlideshow`)
- Desktop shortcut
- Configuration file
- Video cache

## Migration from Old Installation

If you're migrating from `/opt/slideshow`:

1. **Install new version:**
   ```bash
   ./install.sh
   ```

2. **Copy your config (if you customized it):**
   ```bash
   # If you had a custom config at the old location
   cp /opt/slideshow/.photo_slideshow_config.json ~/.photo_slideshow_config.json
   ```

3. **Remove old installation:**
   ```bash
   cd /Applications/PhotoSlideshow
   ./uninstall.sh
   ```

4. **Test the new installation:**
   ```bash
   ./launcher.sh
   ```
