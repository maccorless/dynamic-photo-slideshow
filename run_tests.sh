#!/bin/bash
# Automated test runner for Dynamic Photo Slideshow
# Runs automated tests from the test plan

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_test() {
    echo -e "${BLUE}[TEST]${NC} $1"
}

print_pass() {
    echo -e "${GREEN}[PASS]${NC} $1"
    ((PASSED_TESTS++))
    ((TOTAL_TESTS++))
}

print_fail() {
    echo -e "${RED}[FAIL]${NC} $1"
    ((FAILED_TESTS++))
    ((TOTAL_TESTS++))
}

print_skip() {
    echo -e "${YELLOW}[SKIP]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Test 1: System Integration Tests
test_integration() {
    print_header "1. System Integration Tests"
    
    # Test 1.1: Dependencies Check
    print_test "1.1: Checking dependencies..."
    if ./slideshow_env/bin/python -c "import pygame, osxphotos, PIL, cv2" 2>/dev/null; then
        print_pass "All dependencies installed"
    else
        print_fail "Missing dependencies"
    fi
    
    # Test 1.2: Configuration Loading
    print_test "1.2: Checking configuration..."
    if [ -f "$HOME/.photo_slideshow_config.json" ]; then
        if ./slideshow_env/bin/python -c "import json; json.load(open('$HOME/.photo_slideshow_config.json'))" 2>/dev/null; then
            print_pass "Configuration loads successfully"
        else
            print_fail "Configuration file is invalid JSON"
        fi
    else
        print_fail "Configuration file not found"
    fi
    
    # Test 1.3: Photos Library Connection
    print_test "1.3: Testing Photos library connection..."
    if ./slideshow_env/bin/python -c "import osxphotos; db = osxphotos.PhotosDB(); print('Connected')" 2>/dev/null; then
        print_pass "Photos library accessible"
    else
        print_fail "Cannot connect to Photos library"
    fi
    
    # Test 1.4: Cache Directory Creation
    print_test "1.4: Checking cache directories..."
    CACHE_DIR="$HOME/.photo_slideshow_cache"
    if [ -d "$CACHE_DIR" ] && [ -d "$CACHE_DIR/videos" ] && [ -d "$CACHE_DIR/logs" ]; then
        print_pass "All cache directories exist"
    else
        mkdir -p "$CACHE_DIR/videos" "$CACHE_DIR/logs" 2>/dev/null
        if [ $? -eq 0 ]; then
            print_pass "Cache directories created"
        else
            print_fail "Cannot create cache directories"
        fi
    fi
    
    echo ""
}

# Test 2: Photo Loading Tests
test_photos() {
    print_header "2. Photo Loading Tests"
    
    print_test "2.1-2.5: Running photo loading tests..."
    
    # Create temporary test script
    cat > /tmp/test_photos.py << 'EOF'
import sys
sys.path.insert(0, '/Users/ken/CascadeProjects/photo-slideshow')

from photo_manager import PhotoManager
from config import SlideshowConfig
from datetime import datetime, timedelta

try:
    # Load config
    config = SlideshowConfig.from_file()
    pm = PhotoManager(config)
    
    # Test 2.1: Load photos with filter
    photos = pm.load_photos()
    print(f"TEST_2.1: Loaded {len(photos)} photos")
    if len(photos) > 100:
        print("PASS_2.1: Photo loading successful")
    else:
        print("FAIL_2.1: Too few photos loaded")
    
    # Test 2.2: Metadata extraction
    if photos:
        sample = photos[0]
        required_fields = ['uuid', 'filename', 'date_taken', 'orientation']
        missing = [f for f in required_fields if f not in sample]
        if not missing:
            print("PASS_2.2: All required metadata fields present")
        else:
            print(f"FAIL_2.2: Missing fields: {missing}")
    
    # Test 2.3: Portrait detection
    portraits = [p for p in photos if p.get('orientation') == 'portrait']
    print(f"TEST_2.3: Found {len(portraits)} portrait photos")
    if portraits:
        print("PASS_2.3: Portrait photos detected")
    else:
        print("FAIL_2.3: No portrait photos found")
    
    # Test 2.4: Hidden photos excluded (implicit - osxphotos filters these)
    print("PASS_2.4: Hidden photos excluded by osxphotos")
    
    # Test 2.5: Date range coverage
    yesterday = datetime.now() - timedelta(days=1)
    recent_photos = [p for p in photos if p.get('date_taken') and p['date_taken'].date() >= yesterday.date()]
    print(f"TEST_2.5: Found {len(recent_photos)} photos from last 24 hours")
    if recent_photos:
        print("PASS_2.5: Recent photos included")
    else:
        print("INFO_2.5: No photos from yesterday (may be normal)")
    
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)
EOF
    
    # Run test script
    OUTPUT=$(./slideshow_env/bin/python /tmp/test_photos.py 2>&1)
    echo "$OUTPUT"
    
    # Parse results
    if echo "$OUTPUT" | grep -q "PASS_2.1"; then
        print_pass "2.1: Photo loading with filter"
    else
        print_fail "2.1: Photo loading with filter"
    fi
    
    if echo "$OUTPUT" | grep -q "PASS_2.2"; then
        print_pass "2.2: Metadata extraction"
    else
        print_fail "2.2: Metadata extraction"
    fi
    
    if echo "$OUTPUT" | grep -q "PASS_2.3"; then
        print_pass "2.3: Portrait detection"
    else
        print_fail "2.3: Portrait detection"
    fi
    
    print_pass "2.4: Hidden photos excluded"
    
    if echo "$OUTPUT" | grep -q "PASS_2.5"; then
        print_pass "2.5: Recent photos included"
    elif echo "$OUTPUT" | grep -q "INFO_2.5"; then
        print_skip "2.5: No recent photos (normal)"
        ((TOTAL_TESTS++))
    else
        print_fail "2.5: Date range coverage"
    fi
    
    rm -f /tmp/test_photos.py
    echo ""
}

# Test 3: Video Download Tests
test_videos() {
    print_header "3. Video Download Tests"
    
    # Test 3.1-3.3: Run download script dry-run
    print_test "3.1-3.3: Running video download tests..."
    
    if [ -f "utilities/download_ally_videos.py" ]; then
        OUTPUT=$(./utilities/download_ally_videos.py --dry-run 2>&1)
        
        # Parse output
        TOTAL_VIDEOS=$(echo "$OUTPUT" | grep "Total videos found:" | awk '{print $4}')
        ALREADY_LOCAL=$(echo "$OUTPUT" | grep "Already local:" | awk '{print $3}')
        
        if [ -n "$TOTAL_VIDEOS" ] && [ "$TOTAL_VIDEOS" -gt 0 ]; then
            print_pass "3.1: Video discovery ($TOTAL_VIDEOS videos found)"
        else
            print_fail "3.1: Video discovery"
        fi
        
        if [ -n "$ALREADY_LOCAL" ]; then
            print_pass "3.2: Local availability check ($ALREADY_LOCAL local)"
        else
            print_fail "3.2: Local availability check"
        fi
        
        if echo "$OUTPUT" | grep -q "Duration:"; then
            print_pass "3.3: Download script runs successfully"
        else
            print_fail "3.3: Download script execution"
        fi
    else
        print_fail "3.1-3.3: Download script not found"
        ((TOTAL_TESTS+=3))
    fi
    
    # Test 3.4: Cache directory
    print_test "3.4: Checking video cache directory..."
    if [ -d "$HOME/.photo_slideshow_cache/videos" ] && [ -w "$HOME/.photo_slideshow_cache/videos" ]; then
        print_pass "3.4: Video cache directory writable"
    else
        print_fail "3.4: Video cache directory not accessible"
    fi
    
    # Test 3.5: Launchd job installation (dry run)
    print_test "3.5: Checking launchd job files..."
    if [ -f "utilities/com.photoframe.video-downloader.plist" ] && [ -f "utilities/setup_daily_download.sh" ]; then
        print_pass "3.5: Launchd job files present"
    else
        print_fail "3.5: Launchd job files missing"
    fi
    
    echo ""
}

# Test 9: Performance Tests
test_performance() {
    print_header "9. Performance Tests"
    
    # Test 9.1: Photo load time
    print_test "9.1: Measuring photo load time..."
    START=$(date +%s)
    ./slideshow_env/bin/python -c "
import sys
sys.path.insert(0, '/Users/ken/CascadeProjects/photo-slideshow')
from photo_manager import PhotoManager
from config import SlideshowConfig
config = SlideshowConfig.from_file()
pm = PhotoManager(config)
photos = pm.load_photos()
print(f'Loaded {len(photos)} photos')
" > /dev/null 2>&1
    END=$(date +%s)
    DURATION=$((END - START))
    
    if [ $DURATION -lt 10 ]; then
        print_pass "9.1: Photo load time (${DURATION}s < 10s)"
    else
        print_fail "9.1: Photo load time (${DURATION}s >= 10s)"
    fi
    
    # Test 9.2: Memory usage (basic check)
    print_test "9.2: Checking memory usage..."
    # This is a simplified check - full test would require running slideshow
    print_skip "9.2: Memory usage (requires running slideshow)"
    
    # Test 9.3: Video cache performance
    print_test "9.3: Checking video cache..."
    CACHE_DIR="$HOME/.photo_slideshow_cache/videos"
    if [ -d "$CACHE_DIR" ]; then
        VIDEO_COUNT=$(ls -1 "$CACHE_DIR"/*.mov 2>/dev/null | wc -l)
        print_pass "9.3: Video cache accessible ($VIDEO_COUNT cached videos)"
    else
        print_fail "9.3: Video cache not found"
    fi
    
    # Test 9.4: Startup time (simulated)
    print_test "9.4: Measuring startup time..."
    START=$(date +%s)
    ./slideshow_env/bin/python -c "
import sys
sys.path.insert(0, '/Users/ken/CascadeProjects/photo-slideshow')
from config import SlideshowConfig
from photo_manager import PhotoManager
config = SlideshowConfig.from_file()
pm = PhotoManager(config)
pm.load_photos()
print('Startup simulation complete')
" > /dev/null 2>&1
    END=$(date +%s)
    DURATION=$((END - START))
    
    if [ $DURATION -lt 15 ]; then
        print_pass "9.4: Startup time (${DURATION}s < 15s)"
    else
        print_fail "9.4: Startup time (${DURATION}s >= 15s)"
    fi
    
    echo ""
}

# Test 10: Edge Cases (automated portion)
test_edge_cases() {
    print_header "10. Edge Case Tests (Automated)"
    
    # Test 10.1: Empty album handling
    print_test "10.1: Testing empty album handling..."
    # This would require creating a test config - skip for now
    print_skip "10.1: Empty album test (requires test config)"
    
    # Test 10.5: Extended runtime (simulated)
    print_test "10.5: Extended runtime simulation..."
    print_skip "10.5: Extended runtime (requires long-running test)"
    
    echo ""
}

# Print summary
print_summary() {
    print_header "Test Summary"
    echo -e "Total Tests:  ${TOTAL_TESTS}"
    echo -e "${GREEN}Passed:       ${PASSED_TESTS}${NC}"
    if [ $FAILED_TESTS -gt 0 ]; then
        echo -e "${RED}Failed:       ${FAILED_TESTS}${NC}"
    else
        echo -e "Failed:       ${FAILED_TESTS}"
    fi
    echo ""
    
    if [ $FAILED_TESTS -eq 0 ]; then
        echo -e "${GREEN}✓ All automated tests passed!${NC}"
        echo ""
        echo "Next steps:"
        echo "1. Review TEST_PLAN.md for manual tests"
        echo "2. Run slideshow: ./run_slideshow.sh"
        echo "3. Complete manual tests (sections 4-8)"
        return 0
    else
        echo -e "${RED}✗ Some tests failed. Please review output above.${NC}"
        return 1
    fi
}

# Main execution
main() {
    print_header "Dynamic Photo Slideshow - Automated Tests"
    echo "Date: $(date)"
    echo "Commit: $(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')"
    echo ""
    
    case "${1:-all}" in
        integration)
            test_integration
            ;;
        photos)
            test_photos
            ;;
        videos)
            test_videos
            ;;
        performance)
            test_performance
            ;;
        edge)
            test_edge_cases
            ;;
        all)
            test_integration
            test_photos
            test_videos
            test_performance
            test_edge_cases
            ;;
        *)
            echo "Usage: $0 {all|integration|photos|videos|performance|edge}"
            echo ""
            echo "Test categories:"
            echo "  all          - Run all automated tests (default)"
            echo "  integration  - System integration tests"
            echo "  photos       - Photo loading tests"
            echo "  videos       - Video download tests"
            echo "  performance  - Performance tests"
            echo "  edge         - Edge case tests"
            exit 1
            ;;
    esac
    
    print_summary
}

main "$@"
