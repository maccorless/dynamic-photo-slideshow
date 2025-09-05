# Dynamic Photo Slideshow

A fullscreen photo slideshow application for macOS that connects to Apple Photos with intelligent layout optimization and EXIF data overlays.

## Features

- **Apple Photos Integration**: Direct connection to Photos library using configurable album
- **Fullscreen Display**: Automatic orientation correction and optimal sizing
- **EXIF Overlays**: Date and location information with configurable positioning
- **Smart Navigation**: Auto-advance with keyboard and mouse controls
- **Location Services**: Reverse geocoding with caching for GPS coordinates
- **Configurable Settings**: JSON-based configuration with sensible defaults

## Requirements

- macOS with Photos app
- Python 3.8+
- Photos library access permissions

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create a Photos album named "photoframe" (or configure a different name)

3. Add photos to the album

4. Run the slideshow:
```bash
python main.py
```

## Configuration

The app creates a configuration file at `~/.photo_slideshow_config.json` with these settings:

- **PHOTOS_ALBUM_NAME**: Photos album to use (default: "photoframe")
- **SLIDESHOW_INTERVAL_SECONDS**: Time between slides (default: 10)
- **OVERLAY_PLACEMENT**: "TOP" or "BOTTOM" (default: "TOP")
- **OVERLAY_ALIGNMENT**: "LEFT", "CENTER", or "RIGHT" (default: "CENTER")
- **TRANSITION_EFFECT**: "fade", "crossfade", or "cut" (default: "fade")
- **MONITOR_RESOLUTION**: "auto" or "WIDTHxHEIGHT" (default: "auto")
- **LOGGING_VERBOSE**: Enable detailed logging (default: false)

## Controls

- **Spacebar**: Pause/resume slideshow
- **Left Arrow**: Previous photo
- **Right Arrow**: Next photo
- **Shift**: Show filename overlay
- **Escape**: Exit slideshow
- **Single Click**: Previous photo
- **Double Click**: Next photo

## Phase 1 MVP Features

This initial version includes:
- ✅ Apple Photos integration with album verification
- ✅ Fullscreen display with orientation correction
- ✅ Date and location overlays
- ✅ Auto-advance and keyboard navigation
- ✅ Configuration system with validation
- ✅ Error handling and user feedback
- ✅ Location caching with Nominatim API
- ✅ Advanced filtering by people and places
- ✅ AND/OR logic for filter combinations
- ✅ Configurable photo limits (up to 500)
- ✅ macOS 26.0 compatibility fixes

## Recent Updates & Bug Fixes

### Cache Extension & Incremental Loading System (Latest)
- **Cache Extension**: Dynamic photo cache that grows without full reloads
- **Signal File Detection**: JSON-based mechanism (`~/.photo_slideshow_download_signal.json`) to detect new photo downloads
- **Periodic Cache Refresh**: Configurable interval checks (default: 1 hour) during slideshow runtime
- **Indexed Photo Selection**: Replaced shuffled lists with random index selection for better scalability
- **History Navigation**: Functional previous/next arrow keys with configurable history cache (default: 100 photos)
- **Video File Filtering**: Prevents .mov/.mp4 files from causing display errors
- **Download Script Integration**: Updated download scripts automatically write signal files
- **Startup Photo Loading**: Automatically checks for and loads new photos before slideshow begins

### Advanced Filtering System
- **People Filtering**: Filter photos by specific people names with partial matching
- **Places Filtering**: Filter photos by location with substring matching
- **Logical Operators**: Support for AND/OR logic between people, places, and keywords
- **Configurable Limits**: Set maximum photo count (default: 10,000) via `max_photos_limit`
- **Filter Configuration Helper**: Interactive script (`configure_filters.py`) to analyze library and set filters

### macOS 26.0 Compatibility
- **Smart Album Issues**: Resolved osxphotos compatibility problems with Smart Albums on macOS 26.0
- **Album Detection**: Added fallback logic when album objects return as strings or methods
- **Error Handling**: Improved error messages for album access failures

### Display & Overlay Improvements
- **Portrait Pairing**: Side-by-side display of portrait photos with indexed selection
- **Auto-Advance Timer**: Fixed 10-second auto-advance functionality
- **Overlay Centering**: Fixed text centering issues in overlay backgrounds
- **Background Sizing**: Overlay backgrounds now size exactly to text dimensions
- **Location Accuracy**: Improved Nominatim API zoom level (14) for better city-level results
- **Location Parsing**: Enhanced to handle county/state data when city names unavailable

### Performance & Reliability
- **Photo Caching**: Fixed slideshow crash by properly populating photo cache
- **Error Recovery**: Better handling of missing photos and API failures
- **Threading Safety**: Fixed GUI threading issues with tkinter event loop
- **Logging**: Configurable verbose logging for debugging

### Configuration Enhancements
New configuration options added:
- `cache_refresh_check_interval`: Interval in seconds between new photo checks (default: 3600)
- `photo_history_cache_size`: Number of photos to cache for previous navigation (default: 100)
- `filter_people_names`: Array of people names to filter by
- `filter_by_places`: Array of place names for location filtering
- `people_filter_logic`: "AND" or "OR" logic for people filters
- `places_filter_logic`: "AND" or "OR" logic for places filters
- `overall_filter_logic`: "AND" or "OR" logic combining all filter types
- `max_photos_limit`: Maximum number of photos to load (default: 10,000)

## Future Enhancements (Phase 2+)

- Advanced transition effects
- Performance optimization for large libraries
- GUI configuration interface
- Multiple album support
- Date range filtering
- Keyword-based filtering enhancements
