#!/bin/bash
# Setup script for daily Ally video download automation
# This script installs and manages the launchd job for automatic video downloads

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
PLIST_FILE="$SCRIPT_DIR/com.photoframe.video-downloader.plist"
LAUNCHD_DIR="$HOME/Library/LaunchAgents"
LAUNCHD_PLIST="$LAUNCHD_DIR/com.photoframe.video-downloader.plist"
PYTHON_SCRIPT="$SCRIPT_DIR/download_ally_videos.py"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Function to check if job is loaded
is_job_loaded() {
    launchctl list | grep -q "com.photoframe.video-downloader"
}

# Function to install the job
install_job() {
    print_header "Installing Daily Video Download Job"
    
    # Create LaunchAgents directory if it doesn't exist
    if [ ! -d "$LAUNCHD_DIR" ]; then
        mkdir -p "$LAUNCHD_DIR"
        print_success "Created LaunchAgents directory"
    fi
    
    # Create log directory
    mkdir -p "$HOME/.photo_slideshow_cache/logs"
    print_success "Created log directory"
    
    # Make Python script executable
    chmod +x "$PYTHON_SCRIPT"
    print_success "Made download script executable"
    
    # Copy plist to LaunchAgents
    cp "$PLIST_FILE" "$LAUNCHD_PLIST"
    print_success "Copied plist to LaunchAgents"
    
    # Load the job
    launchctl load "$LAUNCHD_PLIST"
    print_success "Loaded launchd job"
    
    echo ""
    print_success "Installation complete!"
    echo ""
    print_info "The job will run daily at 3:00 AM"
    print_info "Logs will be saved to: ~/.photo_slideshow_cache/logs/"
    echo ""
}

# Function to uninstall the job
uninstall_job() {
    print_header "Uninstalling Daily Video Download Job"
    
    if is_job_loaded; then
        launchctl unload "$LAUNCHD_PLIST"
        print_success "Unloaded launchd job"
    else
        print_warning "Job is not currently loaded"
    fi
    
    if [ -f "$LAUNCHD_PLIST" ]; then
        rm "$LAUNCHD_PLIST"
        print_success "Removed plist from LaunchAgents"
    else
        print_warning "Plist file not found in LaunchAgents"
    fi
    
    echo ""
    print_success "Uninstallation complete!"
    echo ""
}

# Function to check status
check_status() {
    print_header "Daily Video Download Job Status"
    
    if is_job_loaded; then
        print_success "Job is LOADED and ACTIVE"
        echo ""
        print_info "Job details:"
        launchctl list | grep "com.photoframe.video-downloader"
        echo ""
        print_info "Next run: Daily at 3:00 AM"
    else
        print_warning "Job is NOT loaded"
    fi
    
    echo ""
    print_info "Configuration:"
    echo "  Plist file: $LAUNCHD_PLIST"
    echo "  Python script: $PYTHON_SCRIPT"
    echo "  Log directory: ~/.photo_slideshow_cache/logs/"
    echo ""
    
    # Check for recent logs
    LOG_DIR="$HOME/.photo_slideshow_cache/logs"
    if [ -d "$LOG_DIR" ]; then
        LATEST_LOG=$(ls -t "$LOG_DIR"/video_download_*.log 2>/dev/null | head -1)
        if [ -n "$LATEST_LOG" ]; then
            print_info "Latest log file: $LATEST_LOG"
            echo ""
            echo "Last 10 lines:"
            tail -10 "$LATEST_LOG"
        else
            print_warning "No log files found yet"
        fi
    fi
    echo ""
}

# Function to run now (for testing)
run_now() {
    print_header "Running Video Download Now (Test)"
    
    print_info "Running with --verbose flag..."
    echo ""
    
    cd "$PROJECT_DIR"
    "$PROJECT_DIR/slideshow_env/bin/python" "$PYTHON_SCRIPT" --verbose
    
    echo ""
    print_success "Test run complete!"
    echo ""
}

# Function to run dry-run
run_dry() {
    print_header "Dry Run - Show What Would Be Downloaded"
    
    print_info "Running with --dry-run --verbose flags..."
    echo ""
    
    cd "$PROJECT_DIR"
    "$PROJECT_DIR/slideshow_env/bin/python" "$PYTHON_SCRIPT" --dry-run --verbose
    
    echo ""
    print_success "Dry run complete!"
    echo ""
}

# Function to view logs
view_logs() {
    print_header "Recent Download Logs"
    
    LOG_DIR="$HOME/.photo_slideshow_cache/logs"
    
    if [ ! -d "$LOG_DIR" ]; then
        print_warning "Log directory does not exist yet"
        return
    fi
    
    # List all log files
    echo "Available log files:"
    ls -lht "$LOG_DIR"/video_download_*.log 2>/dev/null || print_warning "No log files found"
    echo ""
    
    # Show latest log
    LATEST_LOG=$(ls -t "$LOG_DIR"/video_download_*.log 2>/dev/null | head -1)
    if [ -n "$LATEST_LOG" ]; then
        print_info "Showing latest log: $LATEST_LOG"
        echo ""
        cat "$LATEST_LOG"
    fi
    echo ""
}

# Function to change schedule
change_schedule() {
    print_header "Change Download Schedule"
    
    echo "Current schedule: Daily at 3:00 AM"
    echo ""
    read -p "Enter new hour (0-23): " NEW_HOUR
    read -p "Enter new minute (0-59): " NEW_MINUTE
    
    if ! [[ "$NEW_HOUR" =~ ^[0-9]+$ ]] || [ "$NEW_HOUR" -lt 0 ] || [ "$NEW_HOUR" -gt 23 ]; then
        print_error "Invalid hour. Must be 0-23."
        return 1
    fi
    
    if ! [[ "$NEW_MINUTE" =~ ^[0-9]+$ ]] || [ "$NEW_MINUTE" -lt 0 ] || [ "$NEW_MINUTE" -gt 59 ]; then
        print_error "Invalid minute. Must be 0-59."
        return 1
    fi
    
    # Update the plist file
    sed -i '' "s/<integer>[0-9]*<\/integer>/<integer>$NEW_HOUR<\/integer>/" "$PLIST_FILE"
    
    print_success "Updated schedule to run daily at ${NEW_HOUR}:$(printf "%02d" $NEW_MINUTE)"
    echo ""
    print_warning "You must reinstall the job for changes to take effect:"
    echo "  ./setup_daily_download.sh reinstall"
    echo ""
}

# Function to reinstall (uninstall + install)
reinstall_job() {
    uninstall_job
    sleep 1
    install_job
}

# Main menu
show_menu() {
    print_header "Daily Video Download Manager"
    echo ""
    echo "1) Install daily download job"
    echo "2) Uninstall daily download job"
    echo "3) Check status"
    echo "4) Run download now (test)"
    echo "5) Run dry-run (show what would download)"
    echo "6) View logs"
    echo "7) Change schedule"
    echo "8) Reinstall (uninstall + install)"
    echo "9) Exit"
    echo ""
    read -p "Choose an option (1-9): " choice
    
    case $choice in
        1) install_job ;;
        2) uninstall_job ;;
        3) check_status ;;
        4) run_now ;;
        5) run_dry ;;
        6) view_logs ;;
        7) change_schedule ;;
        8) reinstall_job ;;
        9) exit 0 ;;
        *) print_error "Invalid option" ;;
    esac
}

# Parse command line arguments
if [ $# -eq 0 ]; then
    # No arguments - show menu
    while true; do
        show_menu
        echo ""
        read -p "Press Enter to continue..."
        clear
    done
else
    # Command line mode
    case "$1" in
        install)
            install_job
            ;;
        uninstall)
            uninstall_job
            ;;
        status)
            check_status
            ;;
        run)
            run_now
            ;;
        dry-run)
            run_dry
            ;;
        logs)
            view_logs
            ;;
        reinstall)
            reinstall_job
            ;;
        *)
            echo "Usage: $0 {install|uninstall|status|run|dry-run|logs|reinstall}"
            echo ""
            echo "Or run without arguments for interactive menu"
            exit 1
            ;;
    esac
fi
