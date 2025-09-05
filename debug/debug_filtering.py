#!/usr/bin/env python3
"""
Debug script to trace exactly what photos are being selected during filtering
"""

import osxphotos
from datetime import datetime
import json
import random

def debug_filtering_process():
    """Debug the exact filtering process to see why only recent photos are selected."""
    
    print("Starting filtering debug...")
    photos_db = osxphotos.PhotosDB()
    
    # Get all photos and shuffle them
    all_photos = list(photos_db.photos())
    print(f"Total photos in library: {len(all_photos)}")
    
    # Shuffle all photos first (like in the app)
    random.shuffle(all_photos)
    print("Photos shuffled")
    
    # Filter for people like the app does
    filter_people_names = ["Ally", "Ken"]
    people_logic = "OR"
    max_photos = 5000
    
    matching_photos = []
    
    print(f"\nFiltering for people: {filter_people_names} with {people_logic} logic")
    print("Checking first 50 photos after shuffle...")
    
    for i, photo in enumerate(all_photos[:50]):  # Check first 50 after shuffle
        if not hasattr(photo, 'persons') or not photo.persons:
            continue
            
        # Get people in photo
        photo_people = []
        for person in photo.persons:
            try:
                if hasattr(person, 'name'):
                    name = person.name
                elif hasattr(person, 'display_name'):
                    name = person.display_name
                else:
                    name = str(person)
                
                if name and name != 'None':
                    photo_people.append(name.lower().strip())
            except Exception:
                continue
        
        # Check if matches filter
        matches = any(any(filter_name.lower() in person_name for person_name in photo_people) 
                     for filter_name in filter_people_names)
        
        if matches:
            photo_date = photo.date.strftime('%Y-%m-%d') if photo.date else 'No date'
            print(f"  Match {len(matching_photos)+1}: {photo.original_filename} - {photo_date} - People: {photo_people}")
            matching_photos.append({
                'filename': photo.original_filename,
                'date': photo_date,
                'people': photo_people,
                'uuid': photo.uuid
            })
            
            if len(matching_photos) >= 20:  # Stop after finding 20 matches
                break
    
    print(f"\nFound {len(matching_photos)} matching photos in first 50 shuffled photos")
    
    # Now check what happens if we don't shuffle - get first 50 photos in original order
    print("\n" + "="*60)
    print("Now checking first 50 photos WITHOUT shuffling...")
    
    all_photos_original = list(photos_db.photos())  # Fresh list, no shuffle
    matching_photos_original = []
    
    for i, photo in enumerate(all_photos_original[:50]):
        if not hasattr(photo, 'persons') or not photo.persons:
            continue
            
        # Get people in photo
        photo_people = []
        for person in photo.persons:
            try:
                if hasattr(person, 'name'):
                    name = person.name
                elif hasattr(person, 'display_name'):
                    name = person.display_name
                else:
                    name = str(person)
                
                if name and name != 'None':
                    photo_people.append(name.lower().strip())
            except Exception:
                continue
        
        # Check if matches filter
        matches = any(any(filter_name.lower() in person_name for person_name in photo_people) 
                     for filter_name in filter_people_names)
        
        if matches:
            photo_date = photo.date.strftime('%Y-%m-%d') if photo.date else 'No date'
            print(f"  Match {len(matching_photos_original)+1}: {photo.original_filename} - {photo_date} - People: {photo_people}")
            matching_photos_original.append({
                'filename': photo.original_filename,
                'date': photo_date,
                'people': photo_people,
                'uuid': photo.uuid
            })
            
            if len(matching_photos_original) >= 20:
                break
    
    print(f"\nFound {len(matching_photos_original)} matching photos in first 50 original order photos")
    
    # Save results
    results = {
        'shuffled_matches': matching_photos,
        'original_order_matches': matching_photos_original,
        'total_library_size': len(all_photos)
    }
    
    with open('/Users/ken/CascadeProjects/photo-slideshow/filtering_debug.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to filtering_debug.json")

if __name__ == "__main__":
    debug_filtering_process()
