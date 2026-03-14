#!/bin/bash
# Quick automated test runner - fast version
# Tests critical functionality without long-running operations

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Quick Automated Tests${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

PASSED=0
FAILED=0

# Test 1: Dependencies
echo -n "Testing dependencies... "
if ./slideshow_env/bin/python -c "import pygame, osxphotos, PIL, cv2" 2>/dev/null; then
    echo -e "${GREEN}✓ PASS${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗ FAIL${NC}"
    ((FAILED++))
fi

# Test 2: Configuration
echo -n "Testing configuration... "
if [ -f "$HOME/.photo_slideshow_config.json" ]; then
    if ./slideshow_env/bin/python -c "import json; json.load(open('$HOME/.photo_slideshow_config.json'))" 2>/dev/null; then
        echo -e "${GREEN}✓ PASS${NC}"
        ((PASSED++))
    else
        echo -e "${RED}✗ FAIL${NC}"
        ((FAILED++))
    fi
else
    echo -e "${RED}✗ FAIL (not found)${NC}"
    ((FAILED++))
fi

# Test 3: Photos Library
echo -n "Testing Photos library... "
if ./slideshow_env/bin/python -c "import osxphotos; osxphotos.PhotosDB()" 2>/dev/null; then
    echo -e "${GREEN}✓ PASS${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗ FAIL${NC}"
    ((FAILED++))
fi

# Test 4: Cache Directories
echo -n "Testing cache directories... "
if [ -d "$HOME/.photo_slideshow_cache/videos" ] && [ -d "$HOME/.photo_slideshow_cache/logs" ]; then
    echo -e "${GREEN}✓ PASS${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗ FAIL${NC}"
    ((FAILED++))
fi

# Test 5: Video Download Script
echo -n "Testing video download script... "
if [ -x "utilities/download_ally_videos.py" ]; then
    echo -e "${GREEN}✓ PASS${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗ FAIL${NC}"
    ((FAILED++))
fi

# Test 6: Main Slideshow Script
echo -n "Testing main slideshow script... "
if [ -f "main_pygame.py" ] && [ -f "slideshow_controller.py" ]; then
    echo -e "${GREEN}✓ PASS${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗ FAIL${NC}"
    ((FAILED++))
fi

# Test 7: Run Slideshow Script
echo -n "Testing run script... "
if [ -x "run_slideshow.sh" ]; then
    echo -e "${GREEN}✓ PASS${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗ FAIL${NC}"
    ((FAILED++))
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo "Results: ${GREEN}${PASSED} passed${NC}, ${RED}${FAILED} failed${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All quick tests passed!${NC}"
    echo ""
    echo "System is ready. Next steps:"
    echo "1. Run slideshow: ./run_slideshow.sh"
    echo "2. Complete manual tests from TEST_PLAN.md"
    echo "3. Install video automation: cd utilities && ./setup_daily_download.sh install"
    exit 0
else
    echo -e "${RED}✗ Some tests failed${NC}"
    exit 1
fi
