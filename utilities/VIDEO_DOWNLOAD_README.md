# Automated Ally Video Download System

This system automatically downloads all "Ally" videos from iCloud to your local Mac, ensuring they're always available for the slideshow without freezing or delays.

## Quick Start

### 1. Test the Download Script

First, do a dry run to see what would be downloaded:

```bash
cd /Users/ken/CascadeProjects/photo-slideshow/utilities
./download_ally_videos.py --dry-run --verbose
```

This will show you:
- How many Ally videos exist
- Which ones are already local
- Which ones need to be downloaded
- **Without actually downloading anything**

### 2. Run a Real Download (One-Time)

To download all missing videos now:

```bash
./download_ally_videos.py --verbose
```

This will:
- Find all videos tagged with "Ally"
- Skip videos already available locally
- Download only the videos that are in iCloud
- Save them to `~/.photo_slideshow_cache/videos/`
- Create a detailed log in `~/.photo_slideshow_cache/logs/`

### 3. Setup Daily Automatic Downloads

To schedule automatic daily downloads at 3:00 AM:

```bash
./setup_daily_download.sh install
```

Or use the interactive menu:

```bash
./setup_daily_download.sh
```

Then choose option 1 to install.

## Management Commands

### Interactive Menu

```bash
./setup_daily_download.sh
```

Shows a menu with all options.

### Command Line Options

```bash
./setup_daily_download.sh install      # Install daily job
./setup_daily_download.sh uninstall    # Remove daily job
./setup_daily_download.sh status       # Check if job is running
./setup_daily_download.sh run          # Run download now (test)
./setup_daily_download.sh dry-run      # Show what would download
./setup_daily_download.sh logs         # View recent logs
./setup_daily_download.sh reinstall    # Reinstall job
```

## Download Script Options

### Basic Usage

```bash
./download_ally_videos.py                    # Download all Ally videos
./download_ally_videos.py --verbose          # Show detailed progress
./download_ally_videos.py --dry-run          # Preview without downloading
./download_ally_videos.py --person "John"    # Download videos for different person
```

### Examples

**See what would be downloaded:**
```bash
./download_ally_videos.py --dry-run --verbose
```

**Download with detailed logging:**
```bash
./download_ally_videos.py --verbose
```

**Download videos for a different person:**
```bash
./download_ally_videos.py --person "Sarah" --verbose
```

## How It Works

### Video Detection

The script:
1. Connects to your Photos library using `osxphotos`
2. Searches for all videos tagged with the specified person (default: "Ally")
3. Checks each video's local availability status
4. Downloads only videos that are missing or in iCloud only

### Local Availability Check

A video is considered "local" if:
- It's not marked as `ismissing` in Photos
- It has a valid file path
- The file exists on disk

Videos in iCloud only will be downloaded.

### Download Process

For each video that needs downloading:
1. Uses `osxphotos.export()` with `download_missing=True`
2. Downloads from iCloud if needed
3. Saves to `~/.photo_slideshow_cache/videos/`
4. Names file as `{UUID}.mov` for consistency
5. Logs success/failure

### Caching

- Videos are cached in `~/.photo_slideshow_cache/videos/`
- Once downloaded, they're never re-downloaded (unless you delete the cache)
- The slideshow uses these cached videos for instant playback

## Scheduling Details

### Default Schedule

- **Runs:** Daily at 3:00 AM
- **Why 3 AM:** Low system usage, likely on WiFi, plugged in

### Change Schedule

```bash
./setup_daily_download.sh
# Choose option 7: Change schedule
# Enter new hour (0-23) and minute (0-59)
# Then reinstall: ./setup_daily_download.sh reinstall
```

Or manually edit `com.photoframe.video-downloader.plist`:

```xml
<key>StartCalendarInterval</key>
<dict>
    <key>Hour</key>
    <integer>3</integer>  <!-- Change this -->
    <key>Minute</key>
    <integer>0</integer>  <!-- Change this -->
</dict>
```

Then reinstall:
```bash
./setup_daily_download.sh reinstall
```

## Logs and Monitoring

### Log Locations

- **Daily logs:** `~/.photo_slideshow_cache/logs/video_download_YYYYMMDD.log`
- **Stdout log:** `~/.photo_slideshow_cache/logs/video-downloader-stdout.log`
- **Stderr log:** `~/.photo_slideshow_cache/logs/video-downloader-stderr.log`

### View Logs

```bash
./setup_daily_download.sh logs
```

Or manually:

```bash
cat ~/.photo_slideshow_cache/logs/video_download_$(date +%Y%m%d).log
```

### Check Status

```bash
./setup_daily_download.sh status
```

Shows:
- Whether job is loaded
- Next scheduled run time
- Recent log entries

## Troubleshooting

### Job Not Running

**Check if loaded:**
```bash
launchctl list | grep com.photoframe.video-downloader
```

**Reload the job:**
```bash
./setup_daily_download.sh reinstall
```

### Downloads Failing

**Check logs:**
```bash
./setup_daily_download.sh logs
```

**Common issues:**
- No internet connection
- iCloud Photos not enabled
- Insufficient disk space
- Photos app needs to be open (for some operations)

**Test manually:**
```bash
./download_ally_videos.py --verbose
```

### Videos Still Not Showing in Slideshow

**After downloading, verify:**

1. **Check cache directory:**
   ```bash
   ls -lh ~/.photo_slideshow_cache/videos/
   ```

2. **Verify config:**
   ```bash
   grep video_local_only ~/.photo_slideshow_config.json
   ```
   Should be: `"video_local_only": true`

3. **Restart slideshow** to pick up new videos

### Change Person Filter

**For different person:**
```bash
./download_ally_videos.py --person "John" --verbose
```

**To update daily job:**

Edit `com.photoframe.video-downloader.plist` and change:
```xml
<string>--person</string>
<string>Ally</string>  <!-- Change this -->
```

Then reinstall:
```bash
./setup_daily_download.sh reinstall
```

## Performance

### Download Times

Typical times for downloading from iCloud:

| Video Size | Approx. Time |
|------------|--------------|
| 50MB       | 10-30 seconds |
| 100MB      | 30-60 seconds |
| 200MB      | 1-2 minutes |
| 500MB      | 3-5 minutes |
| 1GB        | 5-10 minutes |

Times vary based on internet speed.

### Disk Space

Videos are stored in `~/.photo_slideshow_cache/videos/`

**Check space used:**
```bash
du -sh ~/.photo_slideshow_cache/videos/
```

**Estimate total space needed:**
- 23 videos @ 100MB each = ~2.3GB
- 50 videos @ 200MB each = ~10GB

## Uninstallation

### Remove Daily Job

```bash
./setup_daily_download.sh uninstall
```

### Remove Downloaded Videos (Optional)

```bash
rm -rf ~/.photo_slideshow_cache/videos/
```

**Warning:** This will delete all cached videos. They'll need to be re-downloaded.

### Remove Logs (Optional)

```bash
rm -rf ~/.photo_slideshow_cache/logs/
```

## Integration with Slideshow

The slideshow automatically uses videos from the cache:

1. **Video filtering** (in `slideshow_controller.py`):
   - Searches for videos with person "Ally"
   - Checks if `video_local_only: true` in config
   - Only includes videos that are locally available

2. **Video playback** (in `pygame_display_manager.py`):
   - Plays videos from local cache
   - No download delay
   - Smooth playback

3. **Cache location:**
   - Same directory: `~/.photo_slideshow_cache/videos/`
   - Videos exported by this script are immediately available to slideshow

## Advanced Usage

### Download Multiple People

Create separate jobs for different people:

```bash
# Copy and modify the plist
cp com.photoframe.video-downloader.plist com.photoframe.video-downloader-john.plist

# Edit to change person name and label
# Then load it
launchctl load ~/Library/LaunchAgents/com.photoframe.video-downloader-john.plist
```

### Custom Schedule (Multiple Times Per Day)

Edit the plist to run multiple times:

```xml
<key>StartCalendarInterval</key>
<array>
    <dict>
        <key>Hour</key>
        <integer>3</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <dict>
        <key>Hour</key>
        <integer>15</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
</array>
```

### Run on Interval Instead of Schedule

Replace `StartCalendarInterval` with:

```xml
<key>StartInterval</key>
<integer>86400</integer>  <!-- Run every 24 hours -->
```

## Files Created

- `download_ally_videos.py` - Main download script
- `setup_daily_download.sh` - Installation and management script
- `com.photoframe.video-downloader.plist` - launchd configuration
- `~/Library/LaunchAgents/com.photoframe.video-downloader.plist` - Installed job
- `~/.photo_slideshow_cache/videos/` - Downloaded videos
- `~/.photo_slideshow_cache/logs/` - Log files

## Support

For issues or questions:
1. Check logs: `./setup_daily_download.sh logs`
2. Run dry-run: `./download_ally_videos.py --dry-run --verbose`
3. Check status: `./setup_daily_download.sh status`
4. Review this README

---

**Last Updated:** October 12, 2025
