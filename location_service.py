"""
Location service for Dynamic Photo Slideshow.
Handles reverse geocoding using Nominatim API with caching.
"""

import json
import logging
import requests
import time
from typing import Optional, Dict, Any
from pathlib import Path
from datetime import datetime, timedelta

from path_config import PathConfig
from slideshow_exceptions import LocationServiceError, GeocodingError


class LocationService:
    """Handles reverse geocoding and location caching."""
    
    def __init__(self, config, path_config: Optional[PathConfig] = None):
        self.config = config
        self.path_config = path_config or PathConfig()
        self.logger = logging.getLogger(__name__)
        self.cache_file = self.path_config.cache_file
        self.cache = {}
        self.load_cache()
        
        # Nominatim API settings
        self.api_url = "https://nominatim.openstreetmap.org/reverse"
        self.headers = {
            'User-Agent': 'PhotoSlideshow/1.0 (Dynamic Photo Slideshow App)'
        }
        
        # Rate limiting settings (Nominatim policy: max 1 request per second)
        self.min_request_interval = 1.0  # seconds between requests
        self.last_request_time = 0
        
        # Retry settings
        self.max_retries = 3
        self.retry_delays = [1, 2, 5]  # seconds to wait between retries
        self.timeout = 10  # request timeout in seconds
    
    def load_cache(self) -> None:
        """Load location cache from file."""
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'r') as f:
                    self.cache = json.load(f)
                self.logger.info(f"Loaded {len(self.cache)} cached locations")
            else:
                self.cache = {}
        except (json.JSONDecodeError, IOError) as e:
            self.logger.error(f"Error loading cache: {e}")
            self.cache = {}
    
    def save_cache(self) -> None:
        """Save location cache to file."""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f, indent=2)
        except IOError as e:
            self.logger.error(f"Error saving cache: {e}")
    
    def get_location_string(self, latitude: float, longitude: float) -> Optional[str]:
        """Get location string for coordinates, using cache when possible."""
        # Create cache key from coordinates (rounded to 4 decimal places for reasonable caching)
        cache_key = f"{round(latitude, 4)},{round(longitude, 4)}"
        
        # Check cache first
        if cache_key in self.cache:
            self.logger.debug(f"Cache hit for coordinates {cache_key}")
            return self.cache[cache_key]
        
        # Make API request
        location_string = self._reverse_geocode(latitude, longitude)
        
        # Cache the result (even if None to avoid repeated failed requests)
        if location_string is not None:
            self.cache[cache_key] = location_string
            self.save_cache()
            self.logger.debug(f"Cached location for {cache_key}: {location_string}")
        else:
            self.logger.debug(f"No location found for {cache_key}")
        
        return location_string
    
    def _reverse_geocode(self, latitude: float, longitude: float) -> Optional[str]:
        """Perform reverse geocoding using Nominatim API with rate limiting."""
        try:
            # Apply rate limiting before making request
            self._apply_rate_limit()
            
            params = {
                'lat': latitude,
                'lon': longitude,
                'format': 'json',
                'accept-language': 'en',  # Force English results
                'zoom': 14,  # More detailed level to get city names
                'addressdetails': 1
            }
            
            response = requests.get(
                self.api_url,
                params=params,
                headers=self.headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            # Update last request time for rate limiting
            self.last_request_time = time.time()
            
            data = response.json()
            return self._extract_location_string(data)
                
        except requests.exceptions.RequestException as e:
            self.logger.warning(f"Geocoding request failed: {e}")
            return None
        except (json.JSONDecodeError, KeyError) as e:
            self.logger.error(f"Error parsing geocoding response: {e}")
            return None
        except Exception as e:
            raise GeocodingError(f"Unexpected error during geocoding: {e}")
        
        return None
    
    def _apply_rate_limit(self) -> None:
        """Apply rate limiting to respect API usage policies."""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last_request
            self.logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _extract_location_string(self, data: Dict[str, Any]) -> Optional[str]:
        """Extract location string from geocoding API response."""
        address = data.get('address', {})
        location_parts = []
        
        # Try to get city, state/province, country in that order
        city = (address.get('city') or 
               address.get('town') or 
               address.get('village') or 
               address.get('hamlet'))
        
        if city:
            location_parts.append(city)
        
        state = (address.get('state') or 
                address.get('province') or 
                address.get('region'))
        
        if state:
            location_parts.append(state)
        
        country = address.get('country')
        if country:
            location_parts.append(country)
        
        return ', '.join(location_parts) if location_parts else None
    
    def clear_cache(self) -> None:
        """Clear all cached location data."""
        self.cache = {}
        if self.cache_file.exists():
            self.cache_file.unlink()
        self.logger.info("Location cache cleared")
