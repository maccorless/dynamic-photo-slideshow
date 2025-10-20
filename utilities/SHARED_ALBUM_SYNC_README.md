# Shared Album Sync Tool

Keep your shared albums in sync with your main Photos library **without creating duplicates**.

## The Problem

- Shared albums (from others) are not accessible to osxphotos or AppleScript
- Manual import creates duplicates if you import the same album multiple times
- You want to keep shared albums in sync as new photos are added

## The Solution

This tool tracks which photos have been imported and only imports **new photos** on subsequent syncs.

## How It Works

1. **First Sync**: You export photos from the shared album and import them
2. **Album Organization**: All imported photos are placed in a local album (default: "Imported from Shared")
3. **Tracking**: The tool records each imported photo's filename and checksum
4. **Future Syncs**: Only new photos (not previously imported) are added
5. **No Duplicates**: Already-imported photos are automatically skipped

## Usage

### Initial Sync

#### Step 1: Get the sync instructions

```bash
python utilities/sync_shared_album.py --album "Ken shared"
```

This will show you the manual export process.

#### Step 2: Export from Photos.app

1. Open **Photos.app**
2. Go to **Shared Albums** → **"Ken shared"**
3. Select all photos: **Cmd+A**
4. **File** → **Export** → **Export Unmodified Original**
5. Save to: **`/tmp/shared_album_export`**

#### Step 3: Import (avoiding duplicates)

```bash
# Dry run first to see what will be imported
python utilities/sync_shared_album.py --album "Ken shared" --import-from-export --dry-run

# Actually import
python utilities/sync_shared_album.py --album "Ken shared" --import-from-export
```

#### Step 4: Clean up

```bash
rm -rf /tmp/shared_album_export
```

### Future Syncs (Getting New Photos)

When new photos are added to the shared album:

1. **Export again** (same process as Step 2 above)
2. **Import again**: `python utilities/sync_shared_album.py --album "Ken shared" --import-from-export`
3. **Only new photos will be imported** - duplicates are automatically skipped!

### Check Sync Status

```bash
python utilities/sync_shared_album.py --status
```

Shows:
- Which albums have been synced
- How many photos imported from each
- When last synced

## Examples

### Sync "Ken shared" album

```bash
# Get instructions
python utilities/sync_shared_album.py --album "Ken shared"

# After exporting from Photos.app:
python utilities/sync_shared_album.py --album "Ken shared" --import-from-export

# Dry run to see what would be imported
python utilities/sync_shared_album.py --album "Ken shared" --import-from-export --dry-run
```

### Sync "Emma & Gene's Wedding" album

```bash
# Get instructions
python utilities/sync_shared_album.py --album "Emma & Gene's Wedding"

# After exporting:
python utilities/sync_shared_album.py --album "Emma & Gene's Wedding" --import-from-export
```

### Use custom export folder

```bash
python utilities/sync_shared_album.py --album "Ken shared" --import-from-export --export-folder ~/Downloads/shared_photos
```

### Use custom target album name

By default, photos are imported into an album called "Imported from Shared". You can customize this:

```bash
# Import into a custom album
python utilities/sync_shared_album.py --album "Ken shared" --import-from-export --target-album "Ken's Photos"

# Or use a more specific name
python utilities/sync_shared_album.py --album "Emma & Gene's Wedding" --import-from-export --target-album "Wedding Photos"
```

## How Duplicate Detection Works

The tool uses two methods to detect duplicates:

1. **Filename matching**: Same filename = likely the same photo
2. **Checksum verification**: MD5 hash of file contents ensures exact match

This means:
- Photos with identical content are skipped (even if exported multiple times)
- Modified photos (edited versions) will be imported as new
- You can safely re-export and re-import without creating duplicates

## Tracking Database

The tool maintains a database at:
```
~/.photo_slideshow_shared_album_sync.json
```

This tracks:
- Which photos have been imported from each album
- Checksums to detect duplicates
- Import dates
- Total photos per album

**Don't delete this file** - it's what prevents duplicates!

## Workflow for Regular Syncing

### Weekly/Monthly Sync Routine

```bash
# 1. Export from Photos.app (manual step)
#    - Open Photos → Shared Albums → "Ken shared"
#    - Cmd+A, Export to /tmp/shared_album_export

# 2. Import new photos only
python utilities/sync_shared_album.py --album "Ken shared" --import-from-export

# 3. Clean up
rm -rf /tmp/shared_album_export

# 4. Repeat for other shared albums
python utilities/sync_shared_album.py --album "Emma & Gene's Wedding" --import-from-export
```

### After Syncing

Clear your slideshow cache to see the new photos:
```bash
rm ~/.photo_slideshow_cache.json
```

Then restart your slideshow.

## Troubleshooting

### "No photos found in export folder"

- Make sure you exported to the correct folder: `/tmp/shared_album_export`
- Check that the export completed successfully in Photos.app
- Verify files exist: `ls /tmp/shared_album_export`

### "Already imported (skipped): X photos"

This is normal! It means those photos were already imported in a previous sync.

### Photos not appearing in slideshow

After importing:
1. Clear cache: `rm ~/.photo_slideshow_cache.json`
2. Restart slideshow
3. Check that photos match your filter criteria (person names, etc.)

### Want to re-import everything

Delete the tracking database:
```bash
rm ~/.photo_slideshow_shared_album_sync.json
```

Then re-import. **Warning**: This will create duplicates if photos were already imported!

## Advanced Options

### Check what would be imported (dry run)

```bash
python utilities/sync_shared_album.py --album "Ken shared" --import-from-export --dry-run
```

### View sync history

```bash
python utilities/sync_shared_album.py --status
```

### Use different export folder

```bash
python utilities/sync_shared_album.py --album "Ken shared" --import-from-export --export-folder ~/Desktop/photos
```

## Limitations

- **Manual export required**: Shared albums cannot be accessed programmatically
- **Export step needed**: You must export from Photos.app before each sync
- **Disk space**: Temporary export folder needs space for all photos
- **Time**: Large albums take time to export and import

## Benefits

✅ **No duplicates** - Already-imported photos are automatically skipped  
✅ **Organized** - All imported photos are placed in a dedicated album  
✅ **Track multiple albums** - Sync as many shared albums as you want  
✅ **Safe to re-run** - Run as often as you like without creating duplicates  
✅ **Incremental sync** - Only new photos are imported  
✅ **Full history** - Tracking database shows what's been imported  
✅ **Easy cleanup** - All imported photos are in one album for easy management  

## Tips

1. **Create a script** for your regular albums:
   ```bash
   #!/bin/bash
   # sync_my_albums.sh
   
   echo "Export 'Ken shared' from Photos.app to /tmp/shared_album_export"
   read -p "Press enter when ready..."
   python utilities/sync_shared_album.py --album "Ken shared" --import-from-export
   rm -rf /tmp/shared_album_export
   
   echo "Export 'Emma & Gene's Wedding' from Photos.app to /tmp/shared_album_export"
   read -p "Press enter when ready..."
   python utilities/sync_shared_album.py --album "Emma & Gene's Wedding" --import-from-export
   rm -rf /tmp/shared_album_export
   
   echo "Done! Clear slideshow cache:"
   rm ~/.photo_slideshow_cache.json
   ```

2. **Set a reminder** to sync weekly/monthly

3. **Check status** before syncing to see when you last synced:
   ```bash
   python utilities/sync_shared_album.py --status
   ```
