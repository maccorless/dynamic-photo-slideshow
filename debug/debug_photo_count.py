#!/usr/bin/env python3
"""
Debug script to compare photo counts between different filtering approaches
"""

import osxphotos
from datetime import datetime
import json

def debug_photo_counts():
    """Compare photo counts between our filtering and direct osxphotos search."""
    
    print("Analyzing photo counts...")
    photos_db = osxphotos.PhotosDB()
    
    # Method 1: Our current filtering approach
    print("\n=== Method 1: Current App Filtering ===")
    all_photos = list(photos_db.photos())
    print(f"Total photos in library: {len(all_photos)}")
    
    # Apply our current filter logic
    filter_people_names = ["Ally", "Ken"]
    people_logic = "OR"
    matching_photos_current = []
    
    for photo in all_photos:
        if not hasattr(photo, 'persons') or not photo.persons:
            continue
            
        # Get people in photo (same logic as app)
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
        
        # Check if matches filter (OR logic)
        matches = any(any(filter_name.lower() in person_name for person_name in photo_people) 
                     for filter_name in filter_people_names)
        
        if matches:
            matching_photos_current.append(photo)
    
    print(f"Photos matching current filter (OR logic): {len(matching_photos_current)}")
    
    # Method 2: Direct osxphotos person search
    print("\n=== Method 2: Direct osxphotos Person Search ===")
    try:
        # Search for photos with Ally
        ally_photos = photos_db.photos(persons=["Ally"])
        print(f"Photos with 'Ally': {len(ally_photos)}")
        
        # Search for photos with Ken  
        ken_photos = photos_db.photos(persons=["Ken"])
        print(f"Photos with 'Ken': {len(ken_photos)}")
        
        # Combined (union)
        ally_set = set(p.uuid for p in ally_photos)
        ken_set = set(p.uuid for p in ken_photos)
        combined_set = ally_set.union(ken_set)
        print(f"Photos with Ally OR Ken (union): {len(combined_set)}")
        
        # Intersection (both)
        intersection_set = ally_set.intersection(ken_set)
        print(f"Photos with Ally AND Ken (intersection): {len(intersection_set)}")
        
    except Exception as e:
        print(f"Error with direct person search: {e}")
    
    # Method 3: Check all person names in library
    print("\n=== Method 3: All Person Names Analysis ===")
    all_person_names = set()
    ally_variations = set()
    ken_variations = set()
    
    for photo in all_photos[:1000]:  # Sample first 1000 photos
        if hasattr(photo, 'persons') and photo.persons:
            for person in photo.persons:
                try:
                    if hasattr(person, 'name') and person.name:
                        name = str(person.name).strip()
                        if name and name != 'None':
                            all_person_names.add(name)
                            if 'ally' in name.lower():
                                ally_variations.add(name)
                            if 'ken' in name.lower():
                                ken_variations.add(name)
                except Exception:
                    continue
    
    print(f"Total unique person names found (sample): {len(all_person_names)}")
    print(f"Ally variations found: {sorted(ally_variations)}")
    print(f"Ken variations found: {sorted(ken_variations)}")
    
    # Method 4: Check why we're getting fewer results
    print("\n=== Method 4: Debugging Current Filter ===")
    
    # Check first 100 matching photos for issues
    sample_matches = matching_photos_current[:100]
    date_issues = 0
    metadata_issues = 0
    
    for photo in sample_matches:
        # Check if date extraction would fail
        try:
            photo_date = getattr(photo, 'date', None)
            if not photo_date:
                date_issues += 1
        except:
            date_issues += 1
            
        # Check if metadata extraction would fail
        try:
            photo_data = {
                'uuid': getattr(photo, 'uuid', 'unknown'),
                'filename': getattr(photo, 'filename', 'unknown.jpg'),
                'path': getattr(photo, 'path', ''),
            }
        except:
            metadata_issues += 1
    
    print(f"Sample of {len(sample_matches)} matching photos:")
    print(f"  Photos with date issues: {date_issues}")
    print(f"  Photos with metadata issues: {metadata_issues}")
    
    return {
        'current_filter_count': len(matching_photos_current),
        'ally_variations': list(ally_variations),
        'ken_variations': list(ken_variations),
        'total_person_names': len(all_person_names)
    }

if __name__ == "__main__":
    results = debug_photo_counts()
    
    with open('/Users/ken/CascadeProjects/photo-slideshow/photo_count_debug.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to photo_count_debug.json")
