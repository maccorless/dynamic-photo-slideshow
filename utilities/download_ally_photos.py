#!/usr/bin/env python3
"""
Simple script to download missing Ally photos using basic osxphotos functionality.
"""

import os
import sys
import tempfile
import subprocess
import logging
from pathlib import Path

# Add the project directory to Python path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

def setup_logging():
    """Set up logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def download_ally_photos(max_photos=5000):
    """Download missing Ally photos using osxphotos export."""
    logger = setup_logging()
    
    logger.info(f"Starting download of up to {max_photos} Ally photos...")
    
    # Create temporary directory for export
    with tempfile.TemporaryDirectory() as temp_dir:
        logger.info(f"Using temporary export directory: {temp_dir}")
        
        # Build osxphotos export command for Ally photos
        cmd = [
            'osxphotos', 'export',
            '--download-missing',  # Download from iCloud if missing
            '--person', 'Ally',    # Filter by person
            '--not-hidden',        # Exclude hidden photos
            '--verbose',
            temp_dir
        ]
        
        # Add photo limit if specified
        if max_photos:
            cmd.extend(['--limit', str(max_photos)])
        
        try:
            logger.info(f"Running: {' '.join(cmd)}")
            logger.info("This may take several minutes depending on photo sizes and internet speed...")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=3600  # 1 hour timeout
            )
            
            if result.returncode == 0:
                logger.info("Download completed successfully!")
                if result.stdout:
                    # Count exported photos from output
                    lines = result.stdout.split('\n')
                    exported_count = 0
                    for line in lines:
                        if 'exported' in line.lower() or 'downloading' in line.lower():
                            logger.info(line.strip())
                        if line.strip().startswith('Exported'):
                            try:
                                exported_count = int(line.split()[1])
                            except:
                                pass
                    
                    if exported_count > 0:
                        logger.info(f"Successfully downloaded {exported_count} photos!")
                    else:
                        logger.info("Download completed - check Photos app for new photos")
                return True
            else:
                logger.error(f"Download failed with return code {result.returncode}")
                if result.stderr:
                    logger.error(f"Error output: {result.stderr}")
                if result.stdout:
                    logger.info(f"Output: {result.stdout}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("Download timed out after 1 hour")
            return False
        except Exception as e:
            logger.error(f"Error during download: {e}")
            return False

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Download missing Ally photos from iCloud")
    parser.add_argument('--max-photos', type=int, default=5000, 
                       help='Maximum number of photos to download (default: 5000)')
    parser.add_argument('--test', action='store_true',
                       help='Test with just 10 photos')
    
    args = parser.parse_args()
    
    if args.test:
        max_photos = 10
        print("TEST MODE: Downloading only 10 photos")
    else:
        max_photos = args.max_photos
    
    print(f"This will download up to {max_photos} missing Ally photos from iCloud.")
    print("The photos will be downloaded into your Photos library.")
    
    response = input("Do you want to proceed? (y/N): ").strip().lower()
    if response not in ['y', 'yes']:
        print("Download cancelled.")
        return
    
    success = download_ally_photos(max_photos)
    
    if success:
        print("\n✅ Download completed!")
        print("You can now run your slideshow to see the improved photo selection.")
    else:
        print("\n❌ Download failed. Check the logs above for details.")

if __name__ == "__main__":
    main()
