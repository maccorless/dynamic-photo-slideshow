#!/bin/bash
# Simple script to run the Dynamic Photo Slideshow

cd "$(dirname "$0")"
source slideshow_env/bin/activate
python main.py
