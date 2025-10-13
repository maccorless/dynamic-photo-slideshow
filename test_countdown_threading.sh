#!/bin/bash
#
# Automated Countdown Threading Test
#
# This script runs the slideshow test and automatically analyzes the results
#

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "========================================"
echo "COUNTDOWN THREADING TEST"
echo "========================================"
echo ""
echo "Instructions:"
echo "1. The slideshow will start"
echo "2. Wait for first slide to appear (2-3 seconds)"
echo "3. Press RIGHT arrow 10 times rapidly"
echo "4. Watch the countdown in top-right corner"
echo "5. Press ESC to exit"
echo ""
echo "Press ENTER to start the test..."
read

# Run slideshow with full logging
echo ""
echo "Starting slideshow with detailed logging..."
echo ""

./slideshow_env/bin/python main_pygame.py 2>&1 | tee countdown_test.log

echo ""
echo "========================================"
echo "TEST COMPLETE - ANALYZING LOGS"
echo "========================================"
echo ""

# Analyze the logs
./analyze_countdown_logs.py countdown_test.log

echo ""
echo "========================================"
echo "LOG FILES"
echo "========================================"
echo ""
echo "Full log:     countdown_test.log"
echo "Analyzer:     ./analyze_countdown_logs.py"
echo ""
echo "To re-analyze: ./analyze_countdown_logs.py countdown_test.log"
echo ""
