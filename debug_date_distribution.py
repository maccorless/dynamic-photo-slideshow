#!/usr/bin/env python3
"""
Debug script to analyze the actual date distribution of photos returned by osxphotos
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import SlideshowConfig
from photo_manager import PhotoManager
from collections import defaultdict
from datetime import datetime

def analyze_date_distribution():
    """Analyze the actual date distribution of photos from osxphotos."""
    
    print("Analyzing date distribution of photos from osxphotos...")
    
    # Load config
    config = SlideshowConfig()
    config.load_config()
    
    # Create photo manager and connect
    photo_manager = PhotoManager(config)
    if not photo_manager._connect_to_photos():
        print("Failed to connect to Photos library")
        return
    
    # Get filter configurations
    filter_people_names = config.get('filter_people_names', [])
    
    print(f"Searching for people: {filter_people_names}")
    
    # Get photos using direct search (same as the slideshow)
    filtered_photos = []
    for person_name in filter_people_names:
        try:
            person_photos = photo_manager.photos_db.photos(persons=[person_name.strip()])
            filtered_photos.extend(person_photos)
            print(f"Found {len(person_photos)} photos with person '{person_name}'")
        except Exception as e:
            print(f"Error searching for person '{person_name}': {e}")
    
    # Remove duplicates
    seen_uuids = set()
    unique_photos = []
    for photo in filtered_photos:
        if photo.uuid not in seen_uuids:
            unique_photos.append(photo)
            seen_uuids.add(photo.uuid)
    
    print(f"Total unique photos: {len(unique_photos)}")
    
    # Analyze dates
    date_counts = defaultdict(int)
    year_counts = defaultdict(int)
    
    for photo in unique_photos:
        try:
            photo_date = getattr(photo, 'date', None)
            if photo_date and hasattr(photo_date, 'year') and hasattr(photo_date, 'month'):
                year_month = f"{photo_date.year}-{photo_date.month:02d}"
                date_counts[year_month] += 1
                year_counts[photo_date.year] += 1
        except Exception as e:
            print(f"Error processing photo date: {e}")
    
    print(f"\nDate distribution by year:")
    for year in sorted(year_counts.keys()):
        print(f"  {year}: {year_counts[year]} photos")
    
    print(f"\nDate distribution by month (showing all):")
    for year_month in sorted(date_counts.keys()):
        print(f"  {year_month}: {date_counts[year_month]} photos")
    
    # Focus on recent months
    recent_months = ['2025-08', '2025-09']
    recent_count = sum(date_counts[month] for month in recent_months if month in date_counts)
    total_count = sum(date_counts.values())
    
    print(f"\nRecent analysis:")
    print(f"Aug/Sep 2025: {recent_count} photos")
    print(f"All other periods: {total_count - recent_count} photos")
    print(f"Recent percentage: {(recent_count / total_count * 100):.1f}%")

if __name__ == "__main__":
    analyze_date_distribution()
