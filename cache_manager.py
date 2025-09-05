"""
Cache management for Dynamic Photo Slideshow.
Handles cache invalidation signals and incremental photo loading.
"""

import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List


class CacheManager:
    """Manages photo cache invalidation and incremental loading."""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.signal_file = Path.home() / '.photo_slideshow_download_signal.json'
        self.last_check_time = None
        
    def write_download_signal(self, photos_added: int, total_photos: int) -> None:
        """Write signal file after downloading new photos."""
        try:
            signal_data = {
                "last_download_timestamp": datetime.now(timezone.utc).isoformat(),
                "photos_added": photos_added,
                "total_photos": total_photos,
                "download_session_id": f"session_{int(datetime.now().timestamp())}"
            }
            
            with open(self.signal_file, 'w') as f:
                json.dump(signal_data, f, indent=2)
                
            self.logger.info(f"Wrote download signal: {photos_added} photos added, {total_photos} total")
            
        except Exception as e:
            self.logger.error(f"Failed to write download signal: {e}")
    
    def check_for_new_photos(self) -> Optional[Dict[str, Any]]:
        """Check if new photos have been downloaded since last check."""
        try:
            if not self.signal_file.exists():
                return None
                
            with open(self.signal_file, 'r') as f:
                signal_data = json.load(f)
            
            # Parse the download timestamp
            download_time = datetime.fromisoformat(signal_data["last_download_timestamp"])
            
            # If this is our first check, record the current time and return the signal
            if self.last_check_time is None:
                self.last_check_time = datetime.now(timezone.utc)
                return signal_data
            
            # Check if download happened after our last check
            if download_time > self.last_check_time:
                self.last_check_time = datetime.now(timezone.utc)
                self.logger.info(f"New photos detected: {signal_data['photos_added']} added")
                return signal_data
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to check for new photos: {e}")
            return None
    
    def should_check_cache(self, last_cache_check: Optional[datetime]) -> bool:
        """Determine if it's time to check for cache updates."""
        if last_cache_check is None:
            return True
            
        check_interval = self.config.get('cache_refresh_check_interval')
        time_since_check = (datetime.now(timezone.utc) - last_cache_check).total_seconds()
        
        return time_since_check >= check_interval
    
    def get_cache_age_info(self) -> Dict[str, Any]:
        """Get information about cache age and download signals."""
        info = {
            "signal_file_exists": self.signal_file.exists(),
            "last_check_time": self.last_check_time,
            "check_interval": self.config.get('cache_refresh_check_interval')
        }
        
        if self.signal_file.exists():
            try:
                with open(self.signal_file, 'r') as f:
                    signal_data = json.load(f)
                info["last_download"] = signal_data.get("last_download")
                info["total_photos"] = signal_data.get("total_photos")
            except Exception as e:
                self.logger.debug(f"Could not read signal file: {e}")
        
        return info
