# Installation Guide

Quick guide to get Photo Slideshow running on a new runtime machine.

## Bootstrap Installation (New Machine)

### Step 1: Download the Installer

On the runtime machine, open Terminal and run:

```bash
curl -O https://raw.githubusercontent.com/maccorless/dynamic-photo-slideshow/photo-video-voice/install.sh
chmod +x install.sh
```

This downloads the installation script directly from GitHub.

### Step 2: Run the Installer

```bash
./install.sh
```

The installer will:
- ✅ Check for Python 3.13+ (guide you to install if missing)
- ✅ Check for git (guide you to install if missing)
- ✅ Clone the repository to `/Applications/PhotoSlideshow`
- ✅ Create a virtual environment
- ✅ Install all Python dependencies
- ✅ Set up your configuration file
- ✅ Create a desktop shortcut
- ✅ Clean video cache and logs

**Installation takes 2-5 minutes** depending on your internet connection.

### Step 3: Run the Slideshow

**Option A: Desktop Shortcut**
- Double-click **PhotoSlideshow** on your Desktop

**Option B: Command Line**
```bash
cd /Applications/PhotoSlideshow
./launcher.sh
```

---

## What Gets Installed

| Item | Location | Purpose |
|------|----------|---------|
| Application Code | `/Applications/PhotoSlideshow/` | Main installation |
| Virtual Environment | `/Applications/PhotoSlideshow/venv/` | Isolated Python packages |
| Configuration | `~/.photo_slideshow_config.json` | Your settings |
| Video Cache | `~/.photo_slideshow_cache/videos/` | Exported video files |
| Desktop Shortcut | `~/Desktop/PhotoSlideshow.command` | Quick launcher |

---

## Prerequisites

### Python 3.13+

**Check if installed:**
```bash
python3 --version
```

**If version is too old (3.12 or earlier):**
- Download Python 3.13+ from [python.org](https://www.python.org/downloads/)
- Or install via Homebrew: `brew install python@3.13`

### Git

**Check if installed:**
```bash
git --version
```

**If not installed:**
```bash
xcode-select --install
```

---

## Common Scenarios

### Scenario 1: Clean Machine (First Time)

```bash
# Download installer
curl -O https://raw.githubusercontent.com/maccorless/dynamic-photo-slideshow/photo-video-voice/install.sh
chmod +x install.sh

# Run installer
./install.sh

# Launch slideshow
cd /Applications/PhotoSlideshow
./launcher.sh
```

### Scenario 2: Migrating from Old Installation

If you have an old installation at `/opt/slideshow`:

```bash
# Install new version first
curl -O https://raw.githubusercontent.com/maccorless/dynamic-photo-slideshow/photo-video-voice/install.sh
chmod +x install.sh
./install.sh

# Copy your old config (if customized)
cp /opt/slideshow/.photo_slideshow_config.json ~/.photo_slideshow_config.json

# Remove old installation
cd /Applications/PhotoSlideshow
./uninstall.sh
```

### Scenario 3: Updating Existing Installation

```bash
cd /Applications/PhotoSlideshow
./update.sh
```

### Scenario 4: Complete Removal

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

---

## Configuration

### First-Time Setup

The installer creates a default config at `~/.photo_slideshow_config.json`.

**Edit settings:**
```bash
nano ~/.photo_slideshow_config.json
```

**Key settings to customize:**
- `PHOTO_TIMER`: Seconds per photo (default: 10)
- `VIDEO_MAX_TIMER`: Max video duration (default: 15)
- `FILTER_PEOPLE`: List of people to show (default: all)
- `voice_commands_enabled`: Enable/disable voice control (default: true)

### Copy Config from Another Machine

```bash
# From your development machine
scp ~/.photo_slideshow_config.json username@runtime-machine:~

# On runtime machine (config will be auto-detected)
# Or manually place it:
mv ~/photo_slideshow_config.json ~/.photo_slideshow_config.json
```

---

## Troubleshooting

### "Python not found" or "Python version too old"

The app requires Python 3.13+.

**Install Python 3.13:**
```bash
# Via Homebrew (recommended)
brew install python@3.13

# Or download from python.org
open https://www.python.org/downloads/
```

**After installing, you may need to use python3.13 explicitly:**
```bash
# Check version
python3.13 --version

# If python3 still points to old version, create alias
alias python3=python3.13
```

### "git not found"

```bash
xcode-select --install
```

### "Permission denied"

Do NOT run with `sudo`. The installer will request admin password when needed.

### "Old installation exists at /opt/slideshow"

This is normal. Install the new version first, then run `./uninstall.sh` to remove the old one.

### Desktop shortcut doesn't work

Recreate it:
```bash
cat > ~/Desktop/PhotoSlideshow.command << 'EOF'
#!/bin/bash
cd "/Applications/PhotoSlideshow" && ./launcher.sh
EOF
chmod +x ~/Desktop/PhotoSlideshow.command
```

### Videos not playing

See [ICLOUD_VIDEOS.md](ICLOUD_VIDEOS.md) for video troubleshooting.

---

## Next Steps

After installation:

1. **Customize your config:**
   ```bash
   nano ~/.photo_slideshow_config.json
   ```

2. **Test the slideshow:**
   ```bash
   cd /Applications/PhotoSlideshow
   ./launcher.sh
   ```

3. **Check for iCloud videos:**
   ```bash
   cd /Applications/PhotoSlideshow
   python download_icloud_videos.py --dry-run
   ```

4. **Read the full deployment guide:**
   - [DEPLOYMENT.md](DEPLOYMENT.md) - Complete deployment documentation
   - [ICLOUD_VIDEOS.md](ICLOUD_VIDEOS.md) - Video management guide
   - [README.md](README.md) - Feature overview

---

## Update Schedule

**To get the latest features and fixes:**

```bash
cd /Applications/PhotoSlideshow
./update.sh
```

**Check what's new:**
```bash
cd /Applications/PhotoSlideshow
git log --oneline -10
```

---

## Support

For issues or questions:
1. Check [DEPLOYMENT.md](DEPLOYMENT.md) troubleshooting section
2. Review logs: `tail -f /Applications/PhotoSlideshow/stderr.log`
3. Check GitHub issues: [github.com/maccorless/dynamic-photo-slideshow](https://github.com/maccorless/dynamic-photo-slideshow)
