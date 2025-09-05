#!/usr/bin/env python3
"""
Debug script to examine what person names actually exist in the Photos library
"""

import osxphotos
from collections import defaultdict

def debug_person_names():
    """Check what person names actually exist in the Photos library."""
    
    print("=== PERSON NAMES DEBUG ===")
    photos_db = osxphotos.PhotosDB()
    
    all_photos = list(photos_db.photos())
    print(f"Total photos: {len(all_photos)}")
    
    # Collect all person names
    person_names = defaultdict(int)
    photos_with_people = 0
    
    print("Scanning for person names...")
    for i, photo in enumerate(all_photos[:5000]):  # Sample first 5000
        if i % 500 == 0:
            print(f"  Processed {i} photos...")
            
        if hasattr(photo, 'persons') and photo.persons:
            photos_with_people += 1
            for person in photo.persons:
                try:
                    # Try different attributes
                    name = None
                    if hasattr(person, 'name') and person.name:
                        name = person.name
                    elif hasattr(person, 'display_name') and person.display_name:
                        name = person.display_name
                    elif hasattr(person, 'fullname') and person.fullname:
                        name = person.fullname
                    
                    if name and name != 'None':
                        person_names[name] += 1
                except Exception as e:
                    continue
    
    print(f"\nFound {photos_with_people} photos with people in first 5000")
    print(f"Found {len(person_names)} unique person names")
    
    # Show most common names
    print("\nMost common person names:")
    sorted_names = sorted(person_names.items(), key=lambda x: x[1], reverse=True)
    for name, count in sorted_names[:20]:
        print(f"  {name}: {count} photos")
    
    # Look specifically for Ally/Ken variations
    print("\nSearching for Ally/Ken variations:")
    ally_names = [name for name in person_names.keys() if 'ally' in name.lower()]
    ken_names = [name for name in person_names.keys() if 'ken' in name.lower()]
    
    print(f"Ally variations: {ally_names}")
    print(f"Ken variations: {ken_names}")
    
    # Test direct osxphotos person search
    print("\nTesting direct osxphotos person queries...")
    try:
        # Get all persons
        all_persons = photos_db.persons
        print(f"Total persons in database: {len(all_persons)}")
        
        # Look for Ally/Ken in persons
        ally_persons = [p for p in all_persons if 'ally' in str(p).lower()]
        ken_persons = [p for p in all_persons if 'ken' in str(p).lower()]
        
        print(f"Ally persons found: {[str(p) for p in ally_persons]}")
        print(f"Ken persons found: {[str(p) for p in ken_persons]}")
        
        # Try searching with exact names
        if ally_persons:
            ally_photos = photos_db.photos(persons=[str(ally_persons[0])])
            print(f"Photos with {ally_persons[0]}: {len(ally_photos)}")
            
        if ken_persons:
            ken_photos = photos_db.photos(persons=[str(ken_persons[0])])
            print(f"Photos with {ken_persons[0]}: {len(ken_photos)}")
            
    except Exception as e:
        print(f"Error with person queries: {e}")
    
    return {
        'total_person_names': len(person_names),
        'ally_variations': ally_names,
        'ken_variations': ken_names,
        'photos_with_people': photos_with_people
    }

if __name__ == "__main__":
    results = debug_person_names()
    print(f"\nResults: {results}")
