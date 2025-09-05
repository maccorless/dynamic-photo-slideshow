#!/usr/bin/env python3
"""
Helper script to configure photo filters for people and places.
"""

import json
import osxphotos
from pathlib import Path

def analyze_library():
    """Analyze Photos library to show available filter options."""
    try:
        db = osxphotos.PhotosDB()
        photos = db.photos()
        
        places = set()
        people_photos = 0
        total_people = 0
        
        print(f"Analyzing {len(photos)} photos in your library...")
        
        # Sample analysis (first 200 photos for speed)
        sample_size = min(200, len(photos))
        for photo in photos[:sample_size]:
            try:
                # Collect places
                if hasattr(photo, 'place') and photo.place:
                    place_name = getattr(photo.place, 'name', str(photo.place))
                    if place_name and place_name != 'None':
                        places.add(place_name)
                
                # Count people
                if hasattr(photo, 'persons') and photo.persons:
                    people_photos += 1
                    total_people += len(photo.persons)
                    
            except Exception:
                continue
        
        print(f"\n📊 Library Analysis (sample of {sample_size} photos):")
        print(f"   Photos with people: {people_photos}")
        print(f"   Total person detections: {total_people}")
        print(f"   Unique places: {len(places)}")
        
        if places:
            print(f"\n📍 Available Places (top 10):")
            for i, place in enumerate(sorted(places)[:10]):
                print(f"   {i+1}. {place}")
        
        return places, people_photos > 0
        
    except Exception as e:
        print(f"Error analyzing library: {e}")
        return set(), False

def update_config_with_filters():
    """Update configuration with advanced filter options."""
    config_path = Path.home() / ".photo_slideshow_config.json"
    
    try:
        # Load existing config
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = json.load(f)
        else:
            config = {}
        
        print("\n🔧 Advanced Filter Configuration:")
        print("1. Filter by specific people names (Ally, Ken, etc.)")
        print("2. Filter by places with substring matching")
        print("3. Combined people AND places filter")
        print("4. Combined people OR places filter")
        print("5. Use album (original behavior)")
        print("6. Show all photos (no filters)")
        
        choice = input("\nChoose option (1-6): ").strip()
        
        if choice == "1":
            print("\nAvailable people: Ally, Ken, Caitlin, Jackie Corless, Joey Corless, etc.")
            people_input = input("Enter people names (comma-separated): ").strip()
            if people_input:
                people_names = [p.strip() for p in people_input.split(',')]
                logic = input("Logic for people (AND/OR, default OR): ").strip().upper() or "OR"
                
                config["filter_people_names"] = people_names
                config["people_filter_logic"] = logic
                config["filter_by_places"] = []
                config["overall_filter_logic"] = "AND"
                print(f"✅ Configured to show photos with people: {people_names} (logic: {logic})")
            else:
                print("❌ No people specified")
                return
                
        elif choice == "2":
            print("\nExample places: Dubai, Chicago, Paris, Maldives")
            print("Substring matching: 'Dub' will match 'Dubai'")
            places_input = input("Enter place filters (comma-separated): ").strip()
            if places_input:
                places = [p.strip() for p in places_input.split(',')]
                logic = input("Logic for places (AND/OR, default OR): ").strip().upper() or "OR"
                
                config["filter_by_places"] = places
                config["places_filter_logic"] = logic
                config["filter_people_names"] = []
                config["overall_filter_logic"] = "AND"
                print(f"✅ Configured to show photos from places: {places} (logic: {logic})")
            else:
                print("❌ No places specified")
                return
                
        elif choice == "3":
            # People AND places
            people_input = input("Enter people names (comma-separated): ").strip()
            places_input = input("Enter place filters (comma-separated): ").strip()
            
            if people_input and places_input:
                people_names = [p.strip() for p in people_input.split(',')]
                places = [p.strip() for p in places_input.split(',')]
                
                config["filter_people_names"] = people_names
                config["filter_by_places"] = places
                config["people_filter_logic"] = "OR"
                config["places_filter_logic"] = "OR"
                config["overall_filter_logic"] = "AND"
                print(f"✅ Configured: ({people_names}) AND ({places})")
            else:
                print("❌ Both people and places required")
                return
                
        elif choice == "4":
            # People OR places
            people_input = input("Enter people names (comma-separated, optional): ").strip()
            places_input = input("Enter place filters (comma-separated, optional): ").strip()
            
            if people_input or places_input:
                people_names = [p.strip() for p in people_input.split(',')] if people_input else []
                places = [p.strip() for p in places_input.split(',')] if places_input else []
                
                config["filter_people_names"] = people_names
                config["filter_by_places"] = places
                config["people_filter_logic"] = "OR"
                config["places_filter_logic"] = "OR"
                config["overall_filter_logic"] = "OR"
                print(f"✅ Configured: ({people_names}) OR ({places})")
            else:
                print("❌ At least one filter required")
                return
                
        elif choice == "5":
            config["filter_by_people"] = False
            config["filter_people_names"] = []
            config["filter_by_places"] = []
            album_name = input("Album name (default 'photoframe'): ").strip() or "photoframe"
            config["album_name"] = album_name
            print(f"✅ Configured to use album: {album_name}")
            
        elif choice == "6":
            config["filter_by_people"] = False
            config["filter_people_names"] = []
            config["filter_by_places"] = []
            config["album_name"] = ""
            print("✅ Configured to show all photos")
            
        else:
            print("❌ Invalid choice")
            return
        
        # Save updated config
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"\n💾 Configuration saved to {config_path}")
        print("🚀 Restart the slideshow to apply new filters!")
        
    except Exception as e:
        print(f"Error updating config: {e}")

if __name__ == "__main__":
    print("📸 Photo Slideshow Filter Configuration")
    print("=" * 40)
    
    # Analyze library first
    analyze_library()
    
    # Configure filters
    update_config_with_filters()
