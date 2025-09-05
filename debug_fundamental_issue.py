#!/usr/bin/env python3
"""
Debug script to fundamentally examine why randomization is failing
"""

import osxphotos
from datetime import datetime
import json
import random

def debug_fundamental_randomization():
    """Deep dive into why randomization isn't working at all."""
    
    print("=== FUNDAMENTAL RANDOMIZATION DEBUG ===")
    photos_db = osxphotos.PhotosDB()
    
    # Get all photos and check their actual dates
    print("\n1. Examining raw photo dates in library...")
    all_photos = list(photos_db.photos())
    print(f"Total photos: {len(all_photos)}")
    
    # Sample dates from different parts of library
    date_samples = []
    for i in [0, 100, 500, 1000, 5000, 10000, len(all_photos)-1]:
        if i < len(all_photos):
            photo = all_photos[i]
            try:
                date = getattr(photo, 'date', None)
                if date:
                    date_samples.append((i, str(date)[:10]))
            except:
                pass
    
    print("Date samples from different positions:")
    for pos, date in date_samples:
        print(f"  Position {pos}: {date}")
    
    # Check if people filtering is the issue
    print("\n2. Testing people filtering...")
    filter_people_names = ["Ally", "Ken"]
    matching_photos = []
    
    # Test first 1000 photos for speed
    test_photos = all_photos[:1000]
    
    for photo in test_photos:
        if not hasattr(photo, 'persons') or not photo.persons:
            continue
            
        # Get people in photo
        photo_people = []
        for person in photo.persons:
            try:
                if hasattr(person, 'name') and person.name:
                    name = person.name
                elif hasattr(person, 'display_name') and person.display_name:
                    name = person.display_name
                else:
                    continue
                
                if name and name != 'None':
                    photo_people.append(name.lower().strip())
            except Exception:
                continue
        
        # Check if matches filter (OR logic)
        matches = any(any(filter_name.lower() in person_name for person_name in photo_people) 
                     for filter_name in filter_people_names)
        
        if matches:
            try:
                date = getattr(photo, 'date', None)
                if date:
                    matching_photos.append((photo, str(date)[:10]))
            except:
                pass
    
    print(f"Found {len(matching_photos)} matching photos in first 1000")
    
    # Check dates of matching photos
    if matching_photos:
        print("\nDates of first 20 matching photos:")
        for i, (photo, date) in enumerate(matching_photos[:20]):
            print(f"  {i+1}. {date}")
    
    # Test shuffling
    print(f"\n3. Testing shuffling on {len(matching_photos)} photos...")
    if len(matching_photos) > 10:
        # Original order dates
        original_dates = [date for _, date in matching_photos[:10]]
        print(f"Original first 10 dates: {original_dates}")
        
        # Shuffle and check
        shuffled_photos = matching_photos.copy()
        random.shuffle(shuffled_photos)
        shuffled_dates = [date for _, date in shuffled_photos[:10]]
        print(f"Shuffled first 10 dates: {shuffled_dates}")
        
        # Check if they're different
        if original_dates == shuffled_dates:
            print("WARNING: Shuffling had no effect!")
        else:
            print("Shuffling appears to work")
    
    # Check if the issue is in the library order itself
    print("\n4. Checking library chronological bias...")
    
    # Get dates from all matching photos
    all_dates = [date for _, date in matching_photos]
    date_counts = {}
    for date in all_dates:
        year_month = date[:7]  # YYYY-MM
        date_counts[year_month] = date_counts.get(year_month, 0) + 1
    
    print("Date distribution in matching photos:")
    for year_month in sorted(date_counts.keys()):
        print(f"  {year_month}: {date_counts[year_month]} photos")
    
    # The real test - what happens when we filter ALL photos, not just first 1000
    print("\n5. Testing full library filtering (this may take time)...")
    print("Filtering all 14k+ photos...")
    
    full_matching = []
    recent_count = 0
    older_count = 0
    
    for i, photo in enumerate(all_photos):
        if i % 1000 == 0:
            print(f"  Processed {i} photos...")
            
        if not hasattr(photo, 'persons') or not photo.persons:
            continue
            
        # Get people in photo
        photo_people = []
        for person in photo.persons:
            try:
                if hasattr(person, 'name') and person.name:
                    name = person.name
                elif hasattr(person, 'display_name') and person.display_name:
                    name = person.display_name
                else:
                    continue
                
                if name and name != 'None':
                    photo_people.append(name.lower().strip())
            except Exception:
                continue
        
        # Check if matches filter
        matches = any(any(filter_name.lower() in person_name for person_name in photo_people) 
                     for filter_name in filter_people_names)
        
        if matches:
            try:
                date = getattr(photo, 'date', None)
                if date:
                    date_str = str(date)[:10]
                    full_matching.append((photo, date_str))
                    
                    if date_str.startswith('2025-08') or date_str.startswith('2025-09'):
                        recent_count += 1
                    else:
                        older_count += 1
            except:
                pass
    
    print(f"\nFull library results:")
    print(f"Total matching photos: {len(full_matching)}")
    print(f"Recent (Aug/Sep 2025): {recent_count}")
    print(f"Older photos: {older_count}")
    print(f"Recent percentage: {recent_count / len(full_matching) * 100:.1f}%")
    
    return {
        'total_matching': len(full_matching),
        'recent_count': recent_count,
        'older_count': older_count,
        'recent_percentage': recent_count / len(full_matching) * 100 if full_matching else 0
    }

if __name__ == "__main__":
    results = debug_fundamental_randomization()
    
    with open('/Users/ken/CascadeProjects/photo-slideshow/fundamental_debug.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to fundamental_debug.json")
