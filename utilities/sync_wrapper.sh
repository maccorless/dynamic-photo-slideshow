#!/bin/bash
cd "/Users/ken/CascadeProjects/photo-slideshow"
source slideshow_env/bin/activate
python sync_photos.py --max-photos 50 --quiet
