#!/bin/bash
# Deploy slideshow config to runtime machine
# Usage: ./deploy_config.sh [target_host]

TARGET_HOST=${1:-"runtime-machine"}

echo "Deploying config to $TARGET_HOST..."

# Copy config file
scp ~/.photo_slideshow_config.json $TARGET_HOST:~/

# Copy any other necessary files
# scp some_other_file $TARGET_HOST:~/ 

echo "Config deployed successfully!"
echo "On $TARGET_HOST, run: mv ~/photo_slideshow_config.json ~/.photo_slideshow_config.json"
