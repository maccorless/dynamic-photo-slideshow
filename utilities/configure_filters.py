#!/usr/bin/env python3
"""
Helper script to configure photo filters for people and places.

Filter config keys:
  FILTER_PEOPLE  - list of people names (OR within list)
  FILTER_PLACES  - list of place substrings (OR within list)
  FILTER_KEYWORD - list of keywords (OR within list)
  FILTER_AND_OR  - how to combine filter types: "AND" or "OR"
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
                if hasattr(photo, 'place') and photo.place:
                    place_name = getattr(photo.place, 'name', str(photo.place))
                    if place_name and place_name != 'None':
                        places.add(place_name)

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
    """Update configuration with filter options."""
    config_path = Path.home() / ".photo_slideshow_config.json"

    try:
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = json.load(f)
        else:
            config = {}

        print("\n🔧 Filter Configuration:")
        print("1. Filter by people names")
        print("2. Filter by places")
        print("3. People AND places (must match both)")
        print("4. People OR places (match either)")
        print("5. Use album (no filters)")
        print("6. Show all photos (no filters)")

        choice = input("\nChoose option (1-6): ").strip()

        if choice == "1":
            people_input = input("Enter people names (comma-separated): ").strip()
            if people_input:
                config["FILTER_PEOPLE"] = [p.strip() for p in people_input.split(',')]
                config["FILTER_PLACES"] = []
                config["FILTER_KEYWORD"] = []
                config["FILTER_AND_OR"] = "AND"
                print(f"✅ Showing photos with: {config['FILTER_PEOPLE']}")
            else:
                print("❌ No people specified")
                return

        elif choice == "2":
            print("Substring matching: 'Dub' will match 'Dubai'")
            places_input = input("Enter place filters (comma-separated): ").strip()
            if places_input:
                config["FILTER_PEOPLE"] = []
                config["FILTER_PLACES"] = [p.strip() for p in places_input.split(',')]
                config["FILTER_KEYWORD"] = []
                config["FILTER_AND_OR"] = "AND"
                print(f"✅ Showing photos from: {config['FILTER_PLACES']}")
            else:
                print("❌ No places specified")
                return

        elif choice == "3":
            people_input = input("Enter people names (comma-separated): ").strip()
            places_input = input("Enter place filters (comma-separated): ").strip()
            if people_input and places_input:
                config["FILTER_PEOPLE"] = [p.strip() for p in people_input.split(',')]
                config["FILTER_PLACES"] = [p.strip() for p in places_input.split(',')]
                config["FILTER_KEYWORD"] = []
                config["FILTER_AND_OR"] = "AND"
                print(f"✅ Showing: {config['FILTER_PEOPLE']} AND {config['FILTER_PLACES']}")
            else:
                print("❌ Both people and places required")
                return

        elif choice == "4":
            people_input = input("Enter people names (comma-separated, optional): ").strip()
            places_input = input("Enter place filters (comma-separated, optional): ").strip()
            if people_input or places_input:
                config["FILTER_PEOPLE"] = [p.strip() for p in people_input.split(',')] if people_input else []
                config["FILTER_PLACES"] = [p.strip() for p in places_input.split(',')] if places_input else []
                config["FILTER_KEYWORD"] = []
                config["FILTER_AND_OR"] = "OR"
                print(f"✅ Showing: {config['FILTER_PEOPLE']} OR {config['FILTER_PLACES']}")
            else:
                print("❌ At least one filter required")
                return

        elif choice == "5":
            config["FILTER_PEOPLE"] = []
            config["FILTER_PLACES"] = []
            config["FILTER_KEYWORD"] = []
            album_name = input("Album name (default 'photoframe'): ").strip() or "photoframe"
            config["album_name"] = album_name
            print(f"✅ Using album: {album_name}")

        elif choice == "6":
            config["FILTER_PEOPLE"] = []
            config["FILTER_PLACES"] = []
            config["FILTER_KEYWORD"] = []
            config["album_name"] = ""
            print("✅ Showing all photos")

        else:
            print("❌ Invalid choice")
            return

        # Clean up any legacy config keys
        for old_key in ['filter_by_people', 'filter_people_names', 'filter_by_places',
                        'filter_by_keywords', 'people_filter_logic', 'places_filter_logic',
                        'overall_filter_logic', 'min_people_count']:
            config.pop(old_key, None)

        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)

        print(f"\n💾 Saved to {config_path}")
        print("🚀 Restart the slideshow to apply!")

    except Exception as e:
        print(f"Error updating config: {e}")

if __name__ == "__main__":
    print("📸 Photo Slideshow Filter Configuration")
    print("=" * 40)
    analyze_library()
    update_config_with_filters()
