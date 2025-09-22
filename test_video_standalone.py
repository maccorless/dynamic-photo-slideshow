#!/usr/bin/env python3
"""
Standalone video test module to isolate video playback issues.
Tests both test videos in complete isolation without any slideshow components.
"""

import tkinter as tk
import subprocess
import time
import os
import sys

class VideoTester:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Video Test - Standalone")
        self.root.configure(bg='black')
        
        # Get screen dimensions
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()
        
        # Make fullscreen
        self.root.geometry(f"{self.screen_width}x{self.screen_height}")
        self.root.attributes('-fullscreen', True)
        
        # Bind escape to exit
        self.root.bind('<Escape>', lambda e: self.root.quit())
        
        # Video paths
        self.short_video = "/Users/ken/CascadeProjects/photo-slideshow/test_videos/short_test_video.mov"
        self.long_video = "/Users/ken/CascadeProjects/photo-slideshow/test_videos/long_test_video.mov"
        
        # Current video process
        self.video_process = None
        
        print("Video Tester initialized")
        print(f"Screen: {self.screen_width}x{self.screen_height}")
        print(f"Short video: {self.short_video}")
        print(f"Long video: {self.long_video}")
        
    def show_message(self, text):
        """Show a text message on screen."""
        # Clear any existing widgets
        for widget in self.root.winfo_children():
            widget.destroy()
            
        label = tk.Label(
            self.root, 
            text=text, 
            font=('Arial', 24), 
            fg='white', 
            bg='black'
        )
        label.pack(expand=True)
        self.root.update()
        
    def play_video(self, video_path, video_name):
        """Play a video using ffplay."""
        print(f"\n=== Playing {video_name} ===")
        print(f"Path: {video_path}")
        
        if not os.path.exists(video_path):
            print(f"ERROR: Video file not found: {video_path}")
            return False
            
        self.show_message(f"Playing {video_name}...")
        time.sleep(1)  # Brief pause to show message
        
        try:
            # Clear screen for video
            for widget in self.root.winfo_children():
                widget.destroy()
            self.root.configure(bg='black')
            self.root.update()
            
            # Get window position
            self.root.update_idletasks()
            window_x = self.root.winfo_rootx()
            window_y = self.root.winfo_rooty()
            
            print(f"Window position: {window_x}, {window_y}")
            
            # Hide Tkinter window during video playback
            print("Hiding Tkinter window to allow video display...")
            self.root.withdraw()  # Hide the window
            
            # ffplay command for fullscreen video
            ffplay_cmd = [
                'ffplay',
                '-i', video_path,
                '-fs',  # Use fullscreen mode instead of manual sizing
                '-autoexit',
                '-loglevel', 'quiet'
            ]
            
            print(f"Running command: {' '.join(ffplay_cmd)}")
            
            # Start ffplay process
            self.video_process = subprocess.Popen(
                ffplay_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            print(f"Started ffplay process: PID {self.video_process.pid}")
            
            # Wait for video to complete
            stdout, stderr = self.video_process.communicate()
            
            print(f"ffplay completed with return code: {self.video_process.returncode}")
            if stdout:
                print(f"STDOUT: {stdout.decode()}")
            if stderr:
                print(f"STDERR: {stderr.decode()}")
                
            self.video_process = None
            
            # Show Tkinter window again after video
            print("Restoring Tkinter window...")
            self.root.deiconify()  # Show the window again
            self.root.lift()       # Bring to front
            
            return True
            
        except Exception as e:
            print(f"ERROR playing video: {e}")
            return False
    
    def run_test(self):
        """Run the complete video test sequence."""
        print("\n=== Starting Video Test Sequence ===")
        
        # Show start message
        self.show_message("Video Test Starting...\nPress ESC to exit")
        time.sleep(2)
        
        # Test short video
        success1 = self.play_video(self.short_video, "Short Video (8.5s)")
        
        if success1:
            self.show_message("Short video completed!\nStarting long video...")
            time.sleep(2)
        else:
            self.show_message("Short video FAILED!")
            time.sleep(3)
        
        # Test long video
        success2 = self.play_video(self.long_video, "Long Video (12.1s)")
        
        if success2:
            self.show_message("Long video completed!\nAll tests finished!")
        else:
            self.show_message("Long video FAILED!")
            
        time.sleep(3)
        
        # Show final results
        if success1 and success2:
            self.show_message("✅ ALL VIDEOS PLAYED SUCCESSFULLY!\nPress ESC to exit")
        else:
            self.show_message("❌ SOME VIDEOS FAILED!\nCheck console output\nPress ESC to exit")

def main():
    print("=== Standalone Video Test ===")
    print("This test will play both test videos in isolation")
    print("Press ESC at any time to exit")
    
    try:
        tester = VideoTester()
        
        # Schedule the test to run after GUI is ready
        tester.root.after(100, tester.run_test)
        
        # Start GUI event loop
        tester.root.mainloop()
        
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"Test failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
