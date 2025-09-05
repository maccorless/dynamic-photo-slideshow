#!/usr/bin/env python3
"""
Debug script to check what dates are actually being displayed in the slideshow
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import SlideshowConfig
from photo_manager import PhotoManager
from datetime import datetime

def debug_slideshow_dates():
    """Debug what photo dates are actually loaded by the slideshow."""
    
    print("Loading slideshow configuration and photos...")
    
    # Load config
    config = SlideshowConfig()
    config_dict = config.config
    
    # Load photos using the same process as the slideshow
    photo_manager = PhotoManager(config_dict)
    photos = photo_manager.load_photos()
    
    print(f"Loaded {len(photos)} photos")
    
    # Analyze dates of loaded photos
    date_counts = {}
    photo_details = []
    
    for i, photo in enumerate(photos[:50]):  # Check first 50 photos
        date_str = photo.get('date', 'No date')
        if date_str and date_str != 'No date':
            try:
                # Parse the date and get year-month
                if 'T' in date_str:
                    date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                else:
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
                
                year_month = date_obj.strftime('%Y-%m')
                date_counts[year_month] = date_counts.get(year_month, 0) + 1
                
                photo_details.append({
                    'index': i + 1,
                    'filename': photo.get('filename', 'Unknown'),
                    'date': date_obj.strftime('%Y-%m-%d'),
                    'year_month': year_month
                })
            except Exception as e:
                print(f"Error parsing date '{date_str}': {e}")
                photo_details.append({
                    'index': i + 1,
                    'filename': photo.get('filename', 'Unknown'),
                    'date': date_str,
                    'year_month': 'Invalid'
                })
        else:
            photo_details.append({
                'index': i + 1,
                'filename': photo.get('filename', 'Unknown'),
                'date': 'No date',
                'year_month': 'No date'
            })
    
    print(f"\nFirst 50 photos in slideshow order:")
    for photo in photo_details:
        print(f"  {photo['index']:2d}. {photo['filename']} - {photo['date']}")
    
    print(f"\nDate distribution in first 50 photos:")
    sorted_dates = sorted(date_counts.items())
    for year_month, count in sorted_dates:
        print(f"  {year_month}: {count} photos")
    
    # Check for recent bias
    recent_count = 0
    older_count = 0
    
    for year_month, count in date_counts.items():
        if year_month >= '2025-08':
            recent_count += count
        else:
            older_count += count
    
    total_with_dates = recent_count + older_count
    if total_with_dates > 0:
        recent_percentage = (recent_count / total_with_dates) * 100
        print(f"\nTemporal analysis of first 50 photos:")
        print(f"Recent photos (Aug 2025+): {recent_count}")
        print(f"Older photos (before Aug 2025): {older_count}")
        print(f"Recent percentage: {recent_percentage:.1f}%")
    
    return photo_details, date_counts

if __name__ == "__main__":
    debug_slideshow_dates()
