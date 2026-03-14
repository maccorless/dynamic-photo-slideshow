# iCloud Video Management

## Overview

The slideshow application can play videos from your Apple Photos library. However, if you use **iCloud Photos with "Optimize Mac Storage"**, some videos may be stored in iCloud and not downloaded to your Mac.

## Problem

When a video is in iCloud but not downloaded locally:
- The slideshow will skip the video (with the recent fix)
- You'll see log messages like: `"Skipping iCloud-only video (not downloaded)"`
- The video won't be available for playback

## Solution: Download Videos from iCloud

### Option 1: Download All Originals (Recommended for Best Experience)

In **Photos.app**:
1. Go to **Photos → Settings** (or **Preferences**)
2. Click the **iCloud** tab
3. Select **Download Originals to this Mac**
4. Wait for all videos to download (may take hours/days depending on library size)

**Pros:**
- All videos will be available
- No ongoing iCloud downloads during slideshow
- Faster slideshow performance

**Cons:**
- Requires significant disk space
- Takes time to download entire library

### Option 2: Download Specific Videos Using Helper Script

Use the included `download_icloud_videos.py` script to download only the videos you want:

```bash
# See what videos are in iCloud (dry run)
python download_icloud_videos.py --dry-run

# Download all iCloud videos
python download_icloud_videos.py

# Download videos from a specific album
python download_icloud_videos.py --album "Vacation 2024"

# Download videos with a specific person
python download_icloud_videos.py --person "John"
```

**How it works:**
1. Scans your Photos library for videos in iCloud
2. Uses `osxphotos` CLI with `--download-missing` option
3. Tells Photos.app via AppleScript to download the videos
4. Exports them to a temporary directory (triggering the download)

**Important Notes:**
- Keep Photos.app **open** during the download process
- The AppleScript interface can be buggy (Photos.app limitation)
- Large videos may take time to download
- You can delete the temporary export directory after completion

### Option 3: Keep "Optimize Mac Storage" and Skip iCloud Videos

If you don't want to download videos:
1. The slideshow will automatically skip iCloud-only videos
2. Only locally available videos will play
3. You'll see log messages about skipped videos

## How the Filtering Works

The application now checks `photo.ismissing` when loading videos:

```python
# In photo_manager.py
if hasattr(photo, 'ismissing') and photo.ismissing:
    self.logger.info(f"Skipping iCloud-only video (not downloaded): {filename}")
    return None
```

This prevents iCloud-only videos from being added to the slideshow cache, avoiding export failures during playback.

## Troubleshooting

### Videos Still Failing to Export

If you see errors like:
```
Failed to export video - export_paths was empty
```

**Possible causes:**
1. Video is in iCloud (check with `download_icloud_videos.py --dry-run`)
2. Video file is corrupted
3. Insufficient disk space for export cache

**Solutions:**
1. Download the video using Photos.app or the helper script
2. Check available disk space (videos are cached in `~/.photo_slideshow_cache/videos/`)
3. Try opening the video in Photos.app to verify it's accessible

### Helper Script Issues

If `download_icloud_videos.py` fails:

**Error: "osxphotos not installed"**
```bash
pip install osxphotos
```

**Error: "AppleScript error"**
- Photos.app's AppleScript interface is buggy
- Try downloading in smaller batches
- Manually download in Photos.app instead

**Downloads are slow**
- This is normal for large videos
- iCloud download speed depends on your internet connection
- Consider downloading overnight

## Checking Video Status

To see which videos are in iCloud vs. local:

```bash
# Using the helper script
python download_icloud_videos.py --dry-run

# Using osxphotos directly
osxphotos query --movies --missing
```

## Configuration

No configuration changes needed. The iCloud filtering is automatic when:
- Video has no local path
- `photo.ismissing` returns `True`

The slideshow will gracefully skip these videos and continue to the next slide.
