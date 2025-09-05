# Utility Scripts

This directory contains utility scripts for managing photos, albums, and system setup.

## Album Management
- `create_album.py` - Creates new albums in Apple Photos
- `create_smart_album.py` - Creates smart albums with filtering criteria
- `add_photos_to_album.py` - Adds photos to existing albums
- `configure_filters.py` - Interactive filter configuration tool

## Photo Download and Sync
- `download_ally_photos.py` - Downloads photos with "Ally" person tag
- `download_missing_photos.py` - Downloads iCloud photos missing locally
- `sync_photos.py` - Synchronizes photos between sources
- `sync_wrapper.sh` - Wrapper script for photo synchronization

## System Setup
- `setup_clean_python.sh` - Sets up clean Python environment
- `setup_sync_schedule.py` - Configures automatic photo sync scheduling

## Documentation
- `create_smart_album_instructions.md` - Instructions for smart album creation

## Usage

These utilities are designed to be run independently for specific tasks:

```bash
# Set up Python environment
./utilities/setup_clean_python.sh

# Create a new album
python utilities/create_album.py

# Download missing iCloud photos
python utilities/download_missing_photos.py

# Configure slideshow filters
python utilities/configure_filters.py
```

Most utilities require the same dependencies as the main slideshow application.
