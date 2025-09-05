#!/usr/bin/env python3
"""
Setup script to create automated hourly photo sync using macOS launchd.
"""

import os
import sys
from pathlib import Path
import json

def create_launchd_plist():
    """Create a launchd plist file for hourly photo syncing."""
    
    project_dir = Path(__file__).parent.absolute()
    sync_script = project_dir / "sync_photos.py"
    
    # Use a shell script wrapper to properly activate the virtual environment
    wrapper_script = project_dir / "sync_wrapper.sh"
    
    # Create wrapper script that activates venv and runs sync
    wrapper_content = f'''#!/bin/bash
cd "{project_dir}"
source slideshow_env/bin/activate
python sync_photos.py --max-photos 50 --quiet
'''
    
    with open(wrapper_script, 'w') as f:
        f.write(wrapper_content)
    
    # Make wrapper executable
    os.chmod(wrapper_script, 0o755)
    
    # Create the plist content using the wrapper script
    plist_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.user.photo-slideshow-sync</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>{wrapper_script}</string>
    </array>
    
    <key>StartInterval</key>
    <integer>3600</integer>
    
    <key>RunAtLoad</key>
    <false/>
    
    <key>StandardOutPath</key>
    <string>{project_dir}/sync_output.log</string>
    
    <key>StandardErrorPath</key>
    <string>{project_dir}/sync_error.log</string>
    
    <key>WorkingDirectory</key>
    <string>{project_dir}</string>
    
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/opt/homebrew/bin</string>
        <key>HOME</key>
        <string>{Path.home()}</string>
    </dict>
</dict>
</plist>'''
    
    # Write to LaunchAgents directory
    launch_agents_dir = Path.home() / "Library" / "LaunchAgents"
    launch_agents_dir.mkdir(exist_ok=True)
    
    plist_file = launch_agents_dir / "com.user.photo-slideshow-sync.plist"
    
    with open(plist_file, 'w') as f:
        f.write(plist_content)
    
    return plist_file

def main():
    """Setup automated photo sync."""
    print("Setting up automated hourly photo sync...")
    
    # Create the launchd plist
    plist_file = create_launchd_plist()
    print(f"Created launchd plist: {plist_file}")
    
    print("\nTo enable the automated sync:")
    print(f"1. Load the service:")
    print(f"   launchctl load {plist_file}")
    print(f"\n2. To disable later:")
    print(f"   launchctl unload {plist_file}")
    print(f"\n3. To check status:")
    print(f"   launchctl list | grep photo-slideshow-sync")
    
    print(f"\nThe sync will:")
    print(f"• Run every hour")
    print(f"• Download up to 50 new photos per run")
    print(f"• Log output to sync_output.log and sync_error.log")
    print(f"• Only download photos matching your Ally filter")
    print(f"• Skip hidden photos automatically")
    
    print(f"\nManual sync commands:")
    print(f"• Check status: python sync_photos.py --status")
    print(f"• Dry run: python sync_photos.py --dry-run")
    print(f"• Manual sync: python sync_photos.py --max-photos 100")

if __name__ == "__main__":
    main()
