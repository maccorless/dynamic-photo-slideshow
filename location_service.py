"""
Location service for Dynamic Photo Slideshow.
Handles reverse geocoding using Nominatim API with caching.
"""

import json
import logging
import requests
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
import time


class LocationService:
    """Handles reverse geocoding and location caching."""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.cache_file = Path.home() / '.photo_slideshow_cache.json'
        self.cache = {}
        self.load_cache()
        
        # Nominatim API settings
        self.api_url = "https://nominatim.openstreetmap.org/reverse"
        self.headers = {
            'User-Agent': 'PhotoSlideshow/1.0 (Dynamic Photo Slideshow App)'
        }
    
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
        """Perform reverse geocoding using Nominatim API."""
        try:
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
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.logger.debug(f"API response for {latitude},{longitude}: {data}")
                return self._format_location(data)
            else:
                self.logger.warning(f"Nominatim API returned status {response.status_code} for {latitude},{longitude}")
                self.logger.debug(f"Response content: {response.text}")
                return None
                
        except requests.RequestException as e:
            self.logger.error(f"Error making reverse geocoding request: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error in reverse geocoding: {e}")
            return None
    
    def _format_location(self, api_data: Dict[str, Any]) -> Optional[str]:
        """Format location data into 'City, CC' format."""
        try:
            address = api_data.get('address', {})
            
            # Try to get city name (prefer city, then town, then village, then county, then state)
            city = (address.get('city') or 
                   address.get('town') or 
                   address.get('village') or 
                   address.get('municipality') or
                   address.get('county') or
                   address.get('state'))
            
            # Get country code
            country_code = address.get('country_code', '').upper()
            
            if city and country_code:
                return f"{city}, {country_code}"
            else:
                self.logger.debug(f"Could not extract city/country from address: {address}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error formatting location data: {e}")
            return None
    
    def clear_cache(self) -> None:
        """Clear all cached location data."""
        self.cache = {}
        if self.cache_file.exists():
            self.cache_file.unlink()
        self.logger.info("Location cache cleared")
