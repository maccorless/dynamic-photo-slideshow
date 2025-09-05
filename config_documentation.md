# Photo Slideshow Configuration Documentation

This document describes all configuration options available in `.photo_slideshow_config.json`.

## Photo Source Configuration

### `album_name` (string, default: "photoframe")
Album name to use from Photos app. Set to empty string or null to use filtering instead of album.   Currently not supported (5-sep-2025) with OS 26 Beta

### `filter_by_people` (boolean, default: false)
Enable filtering by people instead of using album.

### `filter_people_names` (array, default: [])
List of people names to include in slideshow. Uses partial matching - "John" will match "John Smith".

### `filter_by_places` (array, default: [])
List of places to filter by. Uses substring matching - "Paris" will match "Paris, France".

### `filter_by_keywords` (array, default: [])
List of keywords to filter by.

### `people_filter_logic` (string, default: "OR")
Logic for combining people filters: "AND" or "OR".

### `places_filter_logic` (string, default: "OR")
Logic for combining places filters: "AND" or "OR".

### `overall_filter_logic` (string, default: "AND")
Logic for combining all filter types: "AND" or "OR".

### `min_people_count` (integer, default: 1)
Minimum number of people required in photo when using people filter.

### `max_photos_limit` (integer, default: 500)
Maximum number of photos to load into slideshow.

### `shuffle_photos` (boolean, default: true)
Shuffle photos for random order.

## Slideshow Behavior

### `slideshow_interval` (integer, default: 10)
Time between slides in seconds.

### `portrait_pairing` (boolean, default: true)
Enable portrait photo pairing.

## Display Settings

### `MONITOR_RESOLUTION` (string, default: "auto")
Monitor resolution: "auto" or "WIDTHxHEIGHT" like "1920x1080".

### `OVERLAY_PLACEMENT` (string, default: "TOP")
Overlay text placement: "TOP" or "BOTTOM".

### `OVERLAY_ALIGNMENT` (string, default: "CENTER")
Overlay text alignment: "LEFT", "CENTER", or "RIGHT".

### `TRANSITION_EFFECT` (string, default: "fade")
Transition effect: "fade", "crossfade", or "cut".

## Performance & Caching

### `CACHE_SIZE_LIMIT_GB` (integer, default: 20)
Cache size limit in GB.

### `FORCE_CACHE_REFRESH` (boolean, default: false)
Force refresh of photo cache on startup.

## Internal Limits & Constants

### `max_recent_photos` (integer, default: 50)
Maximum photos to track for anti-repetition.

### `fallback_photo_limit` (integer, default: 20)
Fallback photo limit when album is empty.

### `min_fallback_photos` (integer, default: 10)
Minimum fallback photos to show.

### `progress_log_interval` (integer, default: 1000)
Progress logging interval for large libraries.

### `download_batch_size` (integer, default: 100)
Batch size for photo downloads.

### `max_year_percentage` (float, default: 0.3)
Maximum percentage of photos from any single year.

### `cache_refresh_check_interval` (default: 3600)
Interval in seconds between checks for new photos during slideshow runtime.

### `photo_history_cache_size` (default: 100)
Number of previously displayed photo indexes to cache for functional previous navigation.

## Debug & Logging

### `DEBUG_SCALING` (boolean, default: false)
Enable debug scaling information.

### `LOGGING_VERBOSE` (boolean, default: false)
Enable verbose logging output to console and log file.

## Voice Command Configuration

### `voice_commands_enabled` (boolean, default: true)
Enable or disable voice command recognition. Requires microphone access and internet connection for Google Speech API.

### `voice_recognition_engine` (string, default: "google")
Speech recognition engine to use. Currently supports "google" (Google Web Speech API).

### `voice_confidence_threshold` (number, default: 0.7)
Minimum confidence threshold for voice command recognition (0.0 to 1.0).

### `voice_command_timeout` (number, default: 2.0)
Maximum time in seconds to listen for a single voice command.

### `voice_keywords` (object)
Customizable keywords for each voice command:
- `next`: Words that trigger next photo (default: ["next", "forward", "advance"])
- `back`: Words that trigger previous photo (default: ["back", "previous", "backward"])
- `pause`: Words that pause slideshow (default: ["stop", "pause", "halt"])
- `resume`: Words that resume slideshow (default: ["go", "start", "resume", "play"])
