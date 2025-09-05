#!/usr/bin/env python3
"""
Debug script to analyze photo dates and people detection in osxphotos vs macOS Photos
"""

import osxphotos
from datetime import datetime
import json

def analyze_photo_library():
    """Analyze the Photos library to understand date distribution and people detection."""
    
    print("Analyzing Photos library...")
    photos_db = osxphotos.PhotosDB()
    
    # Get all photos
    all_photos = list(photos_db.photos())
    print(f"Total photos in library: {len(all_photos)}")
    
    # Analyze photos with Ally and/or Ken
    ally_photos = []
    ken_photos = []
    both_photos = []
    
    # Date distribution tracking
    date_counts = {}
    
    for photo in all_photos:
        # Get photo date
        if hasattr(photo, 'date') and photo.date:
            year_month = photo.date.strftime('%Y-%m')
            date_counts[year_month] = date_counts.get(year_month, 0) + 1
        
        # Check for people
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
        
        # Check for Ally and Ken
        has_ally = any('ally' in person_name for person_name in photo_people)
        has_ken = any('ken' in person_name for person_name in photo_people)
        
        if has_ally and has_ken:
            both_photos.append({
                'uuid': photo.uuid,
                'date': photo.date.isoformat() if photo.date else None,
                'people': photo_people,
                'filename': photo.original_filename
            })
        elif has_ally:
            ally_photos.append({
                'uuid': photo.uuid,
                'date': photo.date.isoformat() if photo.date else None,
                'people': photo_people,
                'filename': photo.original_filename
            })
        elif has_ken:
            ken_photos.append({
                'uuid': photo.uuid,
                'date': photo.date.isoformat() if photo.date else None,
                'people': photo_people,
                'filename': photo.original_filename
            })
    
    print(f"\nPeople detection results:")
    print(f"Photos with Ally only: {len(ally_photos)}")
    print(f"Photos with Ken only: {len(ken_photos)}")
    print(f"Photos with both Ally and Ken: {len(both_photos)}")
    print(f"Total photos with Ally or Ken: {len(ally_photos) + len(ken_photos) + len(both_photos)}")
    
    # Analyze date distribution for both_photos
    print(f"\nDate distribution for photos with both Ally and Ken:")
    both_dates = {}
    for photo in both_photos:
        if photo['date']:
            try:
                date_obj = datetime.fromisoformat(photo['date'].replace('Z', '+00:00'))
                year_month = date_obj.strftime('%Y-%m')
                both_dates[year_month] = both_dates.get(year_month, 0) + 1
            except:
                continue
    
    # Sort by date and show distribution
    sorted_dates = sorted(both_dates.items())
    for year_month, count in sorted_dates:
        print(f"  {year_month}: {count} photos")
    
    # Show recent vs older distribution
    recent_count = 0
    older_count = 0
    current_year = datetime.now().year
    
    for year_month, count in both_dates.items():
        year = int(year_month.split('-')[0])
        month = int(year_month.split('-')[1])
        
        # Consider Aug 2025 and later as "recent"
        if year == 2025 and month >= 8:
            recent_count += count
        else:
            older_count += count
    
    print(f"\nTemporal distribution:")
    print(f"Recent photos (Aug 2025+): {recent_count}")
    print(f"Older photos (before Aug 2025): {older_count}")
    print(f"Recent percentage: {recent_count / len(both_photos) * 100:.1f}%")
    
    # Save detailed results
    results = {
        'total_photos': len(all_photos),
        'ally_only': len(ally_photos),
        'ken_only': len(ken_photos),
        'both_ally_ken': len(both_photos),
        'date_distribution': both_dates,
        'recent_count': recent_count,
        'older_count': older_count,
        'sample_both_photos': both_photos[:10]  # First 10 for inspection
    }
    
    with open('/Users/ken/CascadeProjects/photo-slideshow/photo_analysis.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\nDetailed results saved to photo_analysis.json")
    
    return results

if __name__ == "__main__":
    analyze_photo_library()
