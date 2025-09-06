# Dynamic Photo Slideshow - Requirements & Dependencies

## System Requirements

### Operating System
- **macOS 10.12 or later** (tested up to macOS 26.0)
- **Apple Photos app** installed and configured
- **Photos library access permissions** granted to the application

### Python Environment
- **Python 3.8 or later** (recommended: Python 3.11+)
- **Virtual environment** recommended for dependency isolation

## Core Dependencies

### Required Python Packages
Install via `pip install -r requirements.txt`:

```
osxphotos>=0.68.0
Pillow>=10.0.0
requests>=2.31.0
pillow-heif>=0.13.0
```

### Package Details

#### osxphotos
- **Purpose**: Interface with Apple Photos library
- **Version**: 0.68.0 or later
- **Features Used**: Photo metadata extraction, album access, GPS coordinates, people detection
- **Compatibility**: Handles macOS version differences and Smart Album issues

#### Pillow (PIL)
- **Purpose**: Image processing and display
- **Version**: 10.0.0 or later
- **Features Used**: Image loading, resizing, orientation correction, overlay rendering
- **Formats Supported**: JPEG, PNG, HEIC, HEIF, GIF, BMP, TIFF, WebP

#### requests
- **Purpose**: HTTP requests for location services
- **Version**: 2.31.0 or later
- **Features Used**: Nominatim API calls for reverse geocoding

#### pillow-heif
- **Purpose**: HEIC/HEIF image format support
- **Version**: 0.13.0 or later
- **Features Used**: Modern iPhone photo format compatibility

### System Libraries
- **tkinter**: GUI framework (included with Python on macOS)
- **threading**: Multi-threading support (Python standard library)
- **json**: Configuration file handling (Python standard library)
- **pathlib**: File system operations (Python standard library)
- **logging**: Application logging (Python standard library)

## Hardware Requirements

### Minimum Specifications
- **RAM**: 4GB (8GB recommended for large photo libraries)
- **Storage**: 1GB free space for cache and temporary files
- **Display**: Any resolution (auto-detects screen dimensions)

### Recommended Specifications
- **RAM**: 8GB or more for libraries with 10,000+ photos
- **Storage**: 5GB+ free space for photo caching
- **Display**: 1920x1080 or higher for optimal viewing experience

## Network Requirements

### Internet Connectivity
- **Required for**: Location services (reverse geocoding)
- **API Used**: Nominatim OpenStreetMap API
- **Fallback**: Works offline but without location overlays
- **Rate Limiting**: Built-in request throttling and caching

## Configuration Requirements

### Photos Library Setup
- **Album Creation**: Create target album in Photos app (or use existing)
- **Photo Organization**: Add desired photos to the target album
- **People Tagging**: Tag people in photos for filtering capabilities
- **Location Data**: Enable GPS/location services for location overlays

### File System Permissions
- **Photos Library Access**: Full disk access or Photos library access
- **Home Directory**: Read/write access for configuration files
- **Cache Directory**: Write access for photo and location caching

## Feature-Specific Requirements

### Cache Extension & Incremental Loading
- **Signal File**: `~/.photo_slideshow_download_signal.json` (auto-created)
- **Cache Manager**: Handles timestamp-based photo detection
- **Background Downloads**: Compatible with download scripts

### Advanced Filtering
- **People Detection**: Requires Photos app people tagging
- **Location Filtering**: Requires GPS metadata in photos
- **Keyword Filtering**: Requires Photos app keyword tagging

### Portrait Photo Pairing
- **EXIF Data**: Requires orientation metadata
- **Dimension Analysis**: Automatic portrait/landscape detection
- **Pairing Logic**: Intelligent matching of portrait photos

### History Navigation
- **Memory Usage**: Configurable history cache (default: 100 photos)
- **Data Structure**: Supports both single photos and photo pairs
- **Navigation**: Functional previous/next arrow keys

## Performance Considerations

### Large Photo Libraries (10,000+ photos)
- **Initial Load**: May take 30-60 seconds for first-time indexing
- **Memory Usage**: ~1-2GB RAM for large libraries
- **Cache Size**: Configurable via `CACHE_SIZE_LIMIT_GB` setting
- **Batch Processing**: Photos processed in configurable batches

### Photo Processing
- **Image Formats**: Automatic format detection and conversion
- **Orientation**: EXIF-based rotation and correction
- **Scaling**: Dynamic scaling based on display resolution
- **Caching**: Intelligent caching of processed images

## Installation Requirements

### Step-by-Step Setup
1. **Python Installation**: Install Python 3.8+ via Homebrew or python.org
2. **Virtual Environment**: Create isolated environment with `python -m venv slideshow_env`
3. **Dependency Installation**: Run `pip install -r requirements.txt`
4. **Photos Setup**: Create album and add photos in Photos app
5. **Configuration**: Run application to generate config file
6. **Permissions**: Grant necessary system permissions when prompted

### Verification Steps
- **Python Version**: `python --version` (should be 3.8+)
- **Package Installation**: `pip list` (verify all packages installed)
- **Photos Access**: Launch Photos app and verify album exists
- **Test Run**: Execute `python main.py` to verify functionality

## Troubleshooting Requirements

### Common Issues
- **Photos Library Access**: Ensure Full Disk Access in System Preferences
- **HEIC Support**: Install pillow-heif for iPhone photo compatibility
- **Network Issues**: Check internet connection for location services
- **Memory Issues**: Reduce `max_photos_limit` for large libraries

### Debug Configuration
- **Verbose Logging**: Set `LOGGING_VERBOSE: true` in config
- **Debug Scaling**: Set `DEBUG_SCALING: true` for image processing debug
- **Log Files**: Check console output for error messages

## Version Compatibility

### macOS Versions
- **Tested**: macOS 10.12 through macOS 26.0
- **Photos App**: All modern versions supported
- **Compatibility Layer**: Automatic detection and adaptation

### Python Versions
- **Minimum**: Python 3.8
- **Recommended**: Python 3.11+
- **Maximum**: Python 3.13 (latest tested)

### Dependency Updates
- **osxphotos**: Regular updates for macOS compatibility
- **Pillow**: Security and performance updates
- **requests**: HTTP library updates
- **pillow-heif**: Format support improvements

## Voice Recognition Commands

### Supported Voice Commands
The slideshow supports hands-free voice control using the system's built-in speech recognition:

#### Navigation Commands
- **"RIGHT"** or **"NEXT"** → Advance to next photo
- **"LEFT"** or **"PREVIOUS"** → Go back to previous photo
- **"GOLLY"** or **"GULLY"** → Resume slideshow (most reliable)
- **"STOP"** or **"PAUSE"** → Pause slideshow

#### Alternative Commands
- **"FORWARD"**, **"ADVANCE"** → Next photo (alternatives)
- **"BACK"**, **"BACKWARD"** → Previous photo (alternatives)
- **"GO"**, **"START"**, **"RESUME"**, **"PLAY"**, **"CONTINUE"** → Resume slideshow
- **"HALT"** → Pause slideshow (alternative)

### Voice Recognition Requirements
- **Microphone Access**: System microphone permissions required
- **Speech Recognition**: Uses Google Speech Recognition API
- **Internet Connection**: Required for voice processing
- **Ambient Noise**: Automatic calibration on startup
- **Confidence Threshold**: Configurable (default: 0.3 for high sensitivity)

### Voice Command Configuration
Located in `~/.photo_slideshow_config.json`:
```json
{
  "voice_commands_enabled": true,
  "voice_recognition_engine": "google",
  "voice_confidence_threshold": 0.3,
  "voice_command_timeout": 2.0,
  "voice_keywords": {
    "next": ["next", "forward", "advance", "right"],
    "back": ["back", "previous", "backward", "left"],
    "pause": ["stop", "pause", "halt"],
    "resume": ["golly", "gully", "go", "start", "resume", "play", "continue"]
  }
}
```

### Voice Recognition Tips
- **Clear Speech**: Speak clearly and at normal volume
- **Single Words**: Use single command words for best recognition
- **"GOLLY" vs "GO"**: "GOLLY" works more reliably than "GO" due to phonetic clarity
- **"LEFT"/"RIGHT"**: More reliable than "BACK"/"FORWARD" for navigation
- **Ambient Noise**: System auto-calibrates but quiet environment helps
- **Retry Commands**: If not recognized, wait 2 seconds and try again

### Troubleshooting Voice Commands
- **No Recognition**: Check microphone permissions in System Preferences
- **Poor Recognition**: Ensure internet connection for Google Speech API
- **Command Delays**: 1.5 second delay is normal for visual feedback
- **Inconsistent Response**: Try alternative command words listed above

## Future Requirements

### Planned Enhancements
- **Local Voice Processing**: Offline speech recognition capabilities
- **Custom Voice Commands**: User-definable command words
- **Voice Feedback**: Audio confirmation of recognized commands
- **Multiple Languages**: Support for non-English voice commands
- **GUI Configuration**: May require additional UI libraries
- **Advanced Transitions**: Potential OpenGL/Metal requirements
- **Multiple Albums**: Enhanced album management capabilities
- **Cloud Integration**: Possible cloud storage API requirements

### Scalability Considerations
- **Enterprise Use**: Database backend for large deployments
- **Multi-User**: User account and permission management
- **Remote Control**: Network API for remote slideshow control
