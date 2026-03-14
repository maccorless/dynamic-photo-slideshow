# Shared Album Import Tool

This tool helps you import photos from shared albums (albums that others have shared with you) into your main Photos library, making them accessible to osxphotos and the slideshow application.

## Why This Is Needed

osxphotos cannot directly access photos in shared albums that others have shared with you. These photos are stored differently in the Photos database. To include them in your slideshow, you need to import them into your main library first.

## Usage

### Step 1: List Available Albums

First, see what albums are available:

```bash
cd /Users/ken/CascadeProjects/photo-slideshow
python utilities/import_shared_album.py --list
```

This will show all albums in Photos.app. You'll need to verify in Photos.app which ones are shared albums.

### Step 2: Test Import (Dry Run)

Before actually importing, do a dry run to see what would happen:

```bash
python utilities/import_shared_album.py --album "Emma & Gene's Wedding" --dry-run
```

Replace `"Emma & Gene's Wedding"` with the actual name of your shared album.

### Step 3: Import the Photos

If the dry run looks good, import the photos:

```bash
python utilities/import_shared_album.py --album "Emma & Gene's Wedding"
```

The script will:
1. Find the album
2. Count the photos
3. Ask for confirmation
4. Import all photos into your main library

## Examples

```bash
# Import from "Ken shared" album
python utilities/import_shared_album.py --album "Ken shared"

# Import from "Emma & Gene's Wedding" album
python utilities/import_shared_album.py --album "Emma & Gene's Wedding"

# Dry run first to test
python utilities/import_shared_album.py --album "Ken shared" --dry-run
```

## Important Notes

1. **Duplicates**: If photos from the shared album already exist in your library, they will be duplicated. Photos.app doesn't automatically detect duplicates during import.

2. **Processing Time**: Importing may take a while for large albums. Be patient and don't close Photos.app during the import.

3. **Slideshow Update**: After importing, you may need to:
   - Restart your slideshow application
   - Or clear the photo cache: `rm ~/.photo_slideshow_cache.json`

4. **Manual Alternative**: If the script doesn't work, you can manually import:
   - Open Photos.app
   - Navigate to the shared album
   - Select all photos (Cmd+A)
   - Right-click → "Import"
   - Photos will be added to your main library

## Troubleshooting

### "Album not found"
- Make sure the album name is spelled exactly as it appears in Photos.app
- Album names are case-sensitive
- Use quotes around album names with spaces

### "Import failed"
- Try the manual import method (see above)
- Make sure Photos.app is not busy with other operations
- Check that you have enough disk space

### Photos not appearing in slideshow
- Clear the cache: `rm ~/.photo_slideshow_cache.json`
- Restart the slideshow application
- Check that the imported photos match your filter criteria (person names, etc.)

## What Happens After Import

Once imported:
- Photos are copied to your main library
- They become accessible to osxphotos
- They will appear in your slideshow (if they match your filters)
- They count toward your iCloud storage (if iCloud Photos is enabled)
- They remain in the shared album (not removed from there)

## Checking Results

After importing, you can verify the photos are accessible:

```bash
cd /Users/ken/CascadeProjects/photo-slideshow
source slideshow_env/bin/activate
python -c "import osxphotos; db = osxphotos.PhotosDB(); print(f'Total photos: {len(db.photos())}')"
```

The count should increase by the number of photos you imported.
