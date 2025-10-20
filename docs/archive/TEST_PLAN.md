# Dynamic Photo Slideshow - Comprehensive Test Plan

**Version:** 3.0  
**Date:** October 12, 2025  
**Status:** Ready for Testing

---

## Test Categories

1. [System Integration Tests](#1-system-integration-tests) - Automated ✅
2. [Photo Loading Tests](#2-photo-loading-tests) - Automated ✅
3. [Video Download Tests](#3-video-download-tests) - Automated ✅
4. [Navigation Tests](#4-navigation-tests) - Manual 👤
5. [Pause/Resume Tests](#5-pauseresume-tests) - Manual 👤
6. [Video Playback Tests](#6-video-playback-tests) - Manual 👤
7. [Overlay Tests](#7-overlay-tests) - Manual 👤
8. [Timer Tests](#8-timer-tests) - Manual 👤
9. [Performance Tests](#9-performance-tests) - Automated ✅
10. [Edge Case Tests](#10-edge-case-tests) - Mixed

---

## 1. System Integration Tests

**Type:** Automated ✅  
**Run Command:** `./run_tests.sh integration`

### Test 1.1: Dependencies Check
**Purpose:** Verify all required packages are installed  
**Automated:** Yes  
**Expected Result:** All dependencies present

### Test 1.2: Configuration Loading
**Purpose:** Verify config file loads correctly  
**Automated:** Yes  
**Expected Result:** Config loaded with all required keys

### Test 1.3: Photos Library Connection
**Purpose:** Verify osxphotos can connect to Photos library  
**Automated:** Yes  
**Expected Result:** Connection successful, library accessible

### Test 1.4: Cache Directory Creation
**Purpose:** Verify cache directories are created  
**Automated:** Yes  
**Expected Result:** All cache dirs exist with correct permissions

---

## 2. Photo Loading Tests

**Type:** Automated ✅  
**Run Command:** `./run_tests.sh photos`

### Test 2.1: Load Photos with Person Filter
**Purpose:** Verify photos load with "Ally" filter  
**Automated:** Yes  
**Expected Result:** 2500+ photos loaded

### Test 2.2: Photo Metadata Extraction
**Purpose:** Verify metadata (date, location, orientation) extracted  
**Automated:** Yes  
**Expected Result:** All required fields present

### Test 2.3: Portrait Photo Detection
**Purpose:** Verify portrait photos identified correctly  
**Automated:** Yes  
**Expected Result:** Portrait photos have orientation='portrait'

### Test 2.4: Hidden Photos Excluded
**Purpose:** Verify hidden photos are filtered out  
**Automated:** Yes  
**Expected Result:** No hidden photos in results

### Test 2.5: Date Range Coverage
**Purpose:** Verify photos span expected date range (including yesterday)  
**Automated:** Yes  
**Expected Result:** Photos from yesterday included

---

## 3. Video Download Tests

**Type:** Automated ✅  
**Run Command:** `./run_tests.sh videos`

### Test 3.1: Video Discovery
**Purpose:** Verify all "Ally" videos are found  
**Automated:** Yes  
**Expected Result:** 23 videos found

### Test 3.2: Local Availability Check
**Purpose:** Verify local vs iCloud status detection  
**Automated:** Yes  
**Expected Result:** Correct local/missing status for each video

### Test 3.3: Download Script Dry Run
**Purpose:** Verify download script identifies videos correctly  
**Automated:** Yes  
**Expected Result:** Script runs without errors, correct counts

### Test 3.4: Cache Directory Structure
**Purpose:** Verify video cache directory exists and is writable  
**Automated:** Yes  
**Expected Result:** Cache dir accessible

### Test 3.5: Launchd Job Installation
**Purpose:** Verify daily job can be installed  
**Automated:** Yes  
**Expected Result:** Job installs and loads successfully

---

## 4. Navigation Tests

**Type:** Manual 👤  
**Instructions:** Run slideshow and test navigation

### Test 4.1: Next Key (Right Arrow)
**Steps:**
1. Start slideshow
2. Press RIGHT arrow key
3. Observe slide change

**Expected Result:** Advances to next slide immediately  
**Status:** ⬜ Not Tested | ✅ Pass | ❌ Fail

### Test 4.2: Back Key (Left Arrow)
**Steps:**
1. Start slideshow
2. Advance 3 slides
3. Press LEFT arrow key
4. Observe slide change

**Expected Result:** Returns to previous slide  
**Status:** ⬜ Not Tested | ✅ Pass | ❌ Fail

### Test 4.3: Multiple Forward Navigation
**Steps:**
1. Start slideshow
2. Press RIGHT arrow 5 times quickly
3. Observe each slide change

**Expected Result:** All 5 advances work, no skipped slides  
**Status:** ⬜ Not Tested | ✅ Pass | ❌ Fail

### Test 4.4: Multiple Back Navigation
**Steps:**
1. Start slideshow
2. Advance 5 slides
3. Press LEFT arrow 3 times
4. Observe navigation

**Expected Result:** Goes back 3 slides correctly  
**Status:** ⬜ Not Tested | ✅ Pass | ❌ Fail

### Test 4.5: Navigation History Boundary
**Steps:**
1. Start slideshow
2. Press LEFT arrow (at beginning)
3. Observe behavior

**Expected Result:** Stays at first slide or wraps to end  
**Status:** ⬜ Not Tested | ✅ Pass | ❌ Fail

---

## 5. Pause/Resume Tests

**Type:** Manual 👤  
**Instructions:** Run slideshow and test pause functionality

### Test 5.1: Pause Photo Slide
**Steps:**
1. Start slideshow on photo
2. Wait 3 seconds
3. Press SPACE
4. Observe countdown timer

**Expected Result:** Countdown freezes at current value  
**Status:** ⬜ Not Tested | ✅ Pass | ❌ Fail

### Test 5.2: Resume Photo Slide
**Steps:**
1. Pause photo slide (Test 5.1)
2. Wait 5 seconds
3. Press SPACE again
4. Observe countdown

**Expected Result:** Countdown resumes from paused value  
**Status:** ⬜ Not Tested | ✅ Pass | ❌ Fail

### Test 5.3: Pause Video Slide
**Steps:**
1. Navigate to video slide
2. Wait for video to start playing
3. Press SPACE
4. Observe video playback

**Expected Result:** Video pauses, audio stops  
**Status:** ⬜ Not Tested | ✅ Pass | ❌ Fail

### Test 5.4: Resume Video Slide
**Steps:**
1. Pause video (Test 5.3)
2. Wait 3 seconds
3. Press SPACE
4. Observe video

**Expected Result:** Video resumes from pause point  
**Status:** ⬜ Not Tested | ✅ Pass | ❌ Fail

### Test 5.5: Navigate While Paused (Photo)
**Steps:**
1. Pause on photo slide
2. Press RIGHT arrow
3. Observe slide change
4. Check if still paused

**Expected Result:** Advances to next slide, remains paused  
**Status:** ⬜ Not Tested | ✅ Pass | ❌ Fail

### Test 5.6: Navigate While Paused (Video)
**Steps:**
1. Pause on video slide
2. Press RIGHT arrow
3. Observe slide change
4. Check display

**Expected Result:** Advances to next slide, remains paused  
**Known Issue:** Video first frame may not display (logged bug)  
**Status:** ⬜ Not Tested | ✅ Pass | ❌ Fail

### Test 5.7: Unpause After Navigation
**Steps:**
1. Pause on photo
2. Navigate forward 2 slides
3. Press SPACE to unpause
4. Observe timer

**Expected Result:** Timer starts counting down from 10s  
**Status:** ⬜ Not Tested | ✅ Pass | ❌ Fail

---

## 6. Video Playback Tests

**Type:** Manual 👤  
**Instructions:** Run slideshow and test video functionality

### Test 6.1: Video Auto-Play
**Steps:**
1. Start slideshow
2. Wait for video slide to appear
3. Observe video

**Expected Result:** Video starts playing automatically  
**Status:** ⬜ Not Tested | ✅ Pass | ❌ Fail

### Test 6.2: Video Audio
**Steps:**
1. Navigate to video with audio
2. Listen for sound
3. Check volume

**Expected Result:** Audio plays clearly  
**Status:** ⬜ Not Tested | ✅ Pass | ❌ Fail

### Test 6.3: Video Completion
**Steps:**
1. Navigate to short video
2. Let it play to completion
3. Observe behavior

**Expected Result:** Advances to next slide automatically  
**Status:** ⬜ Not Tested | ✅ Pass | ❌ Fail

### Test 6.4: Portrait Video Display
**Steps:**
1. Navigate to portrait-oriented video
2. Observe display

**Expected Result:** Video fills screen appropriately, no distortion  
**Status:** ⬜ Not Tested | ✅ Pass | ❌ Fail

### Test 6.5: Landscape Video Display
**Steps:**
1. Navigate to landscape video
2. Observe display

**Expected Result:** Video fills screen, correct aspect ratio  
**Status:** ⬜ Not Tested | ✅ Pass | ❌ Fail

### Test 6.6: Video Overlays
**Steps:**
1. Navigate to video
2. Observe overlays (date, location, video count)
3. Check positioning

**Expected Result:** All overlays visible and correctly positioned  
**Status:** ⬜ Not Tested | ✅ Pass | ❌ Fail

---

## 7. Overlay Tests

**Type:** Manual 👤  
**Instructions:** Run slideshow and verify overlays

### Test 7.1: Date Overlay on Photos
**Steps:**
1. Navigate to photo with known date
2. Check date overlay (bottom left)
3. Verify format

**Expected Result:** Date displays in "Month Day, Year" format  
**Status:** ⬜ Not Tested | ✅ Pass | ❌ Fail

### Test 7.2: Location Overlay on Photos
**Steps:**
1. Navigate to photo with GPS data
2. Check location overlay (bottom right)
3. Verify text

**Expected Result:** Location displays correctly  
**Status:** ⬜ Not Tested | ✅ Pass | ❌ Fail

### Test 7.3: Photo Without Location
**Steps:**
1. Navigate to photo without GPS
2. Check for location overlay

**Expected Result:** No location overlay shown  
**Status:** ⬜ Not Tested | ✅ Pass | ❌ Fail

### Test 7.4: Video Info Overlay
**Steps:**
1. Navigate to video
2. Check top-left corner
3. Verify "Video X/Y" text

**Expected Result:** Shows "Video 1/23" (or similar)  
**Status:** ⬜ Not Tested | ✅ Pass | ❌ Fail

### Test 7.5: Overlay Readability
**Steps:**
1. Navigate through 10 slides
2. Check overlay contrast on light/dark backgrounds
3. Verify all text is readable

**Expected Result:** All overlays readable on all backgrounds  
**Status:** ⬜ Not Tested | ✅ Pass | ❌ Fail

---

## 8. Timer Tests

**Type:** Manual 👤  
**Instructions:** Run slideshow and verify timer behavior

### Test 8.1: Photo Timer Duration
**Steps:**
1. Start slideshow on photo
2. Time from display to auto-advance
3. Record duration

**Expected Result:** Advances after 10 seconds  
**Status:** ⬜ Not Tested | ✅ Pass | ❌ Fail  
**Actual Duration:** _____ seconds

### Test 8.2: Video Timer Duration
**Steps:**
1. Navigate to video
2. Time from start to auto-advance
3. Record duration

**Expected Result:** Advances after 12 seconds (or video length)  
**Status:** ⬜ Not Tested | ✅ Pass | ❌ Fail  
**Actual Duration:** _____ seconds

### Test 8.3: Countdown Display
**Steps:**
1. Start slideshow
2. Watch countdown timer (top-right)
3. Verify it counts down

**Expected Result:** Shows 10, 9, 8... down to 1  
**Status:** ⬜ Not Tested | ✅ Pass | ❌ Fail

### Test 8.4: Timer Cancellation on Navigation
**Steps:**
1. Start slideshow
2. Wait 5 seconds
3. Press RIGHT arrow
4. Observe new slide timer

**Expected Result:** New slide starts fresh 10s timer  
**Status:** ⬜ Not Tested | ✅ Pass | ❌ Fail

### Test 8.5: Timer After Pause/Resume
**Steps:**
1. Start slideshow
2. Wait 3 seconds (timer at 7)
3. Pause
4. Wait 5 seconds
5. Resume
6. Observe timer

**Expected Result:** Timer resumes at 7 and counts down  
**Status:** ⬜ Not Tested | ✅ Pass | ❌ Fail

---

## 9. Performance Tests

**Type:** Automated ✅  
**Run Command:** `./run_tests.sh performance`

### Test 9.1: Photo Load Time
**Purpose:** Verify photos load within acceptable time  
**Automated:** Yes  
**Expected Result:** < 5 seconds for 2500 photos

### Test 9.2: Memory Usage
**Purpose:** Check memory consumption over time  
**Automated:** Yes  
**Expected Result:** < 1GB RAM after 100 slides

### Test 9.3: Video Cache Performance
**Purpose:** Verify cached videos load quickly  
**Automated:** Yes  
**Expected Result:** < 1 second to start playback

### Test 9.4: Startup Time
**Purpose:** Measure time from launch to first slide  
**Automated:** Yes  
**Expected Result:** < 10 seconds

---

## 10. Edge Case Tests

**Type:** Mixed (Automated + Manual)

### Test 10.1: Empty Album (Automated ✅)
**Purpose:** Verify behavior with no photos  
**Automated:** Yes  
**Expected Result:** Graceful error message

### Test 10.2: Single Photo (Manual 👤)
**Steps:**
1. Configure with single photo
2. Start slideshow
3. Try navigation

**Expected Result:** Shows single photo, navigation disabled or wraps  
**Status:** ⬜ Not Tested | ✅ Pass | ❌ Fail

### Test 10.3: Corrupted Video (Manual 👤)
**Steps:**
1. Add corrupted video to cache
2. Navigate to it
3. Observe behavior

**Expected Result:** Skips to next slide with error log  
**Status:** ⬜ Not Tested | ✅ Pass | ❌ Fail

### Test 10.4: Network Disconnection (Manual 👤)
**Steps:**
1. Start slideshow
2. Disconnect WiFi
3. Continue using slideshow

**Expected Result:** Works normally (all local)  
**Status:** ⬜ Not Tested | ✅ Pass | ❌ Fail

### Test 10.5: Extended Runtime (Automated ✅)
**Purpose:** Verify stability over long period  
**Automated:** Yes (simulated)  
**Expected Result:** No memory leaks, no crashes after 1000 slides

---

## Test Execution

### Automated Tests

Run all automated tests:
```bash
./run_tests.sh all
```

Run specific category:
```bash
./run_tests.sh integration
./run_tests.sh photos
./run_tests.sh videos
./run_tests.sh performance
```

### Manual Tests

1. **Print this document** or keep it open
2. **Start slideshow:** `./run_slideshow.sh`
3. **Work through each manual test** in order
4. **Mark status** as you complete each test
5. **Note any failures** with details

### Test Results Template

Copy this for your test session:

```
=== Test Session ===
Date: ___________
Tester: ___________
Commit: ___________

Navigation Tests:
- Test 4.1: ⬜ | Notes: ___________
- Test 4.2: ⬜ | Notes: ___________
[etc...]

Pause/Resume Tests:
- Test 5.1: ⬜ | Notes: ___________
[etc...]

Summary:
- Total Tests: ___
- Passed: ___
- Failed: ___
- Known Issues: ___
```

---

## Success Criteria

### Must Pass (Critical)
- All navigation tests (4.1-4.5)
- All pause/resume tests (5.1-5.7)
- Video playback (6.1-6.3)
- Timer accuracy (8.1-8.4)

### Should Pass (Important)
- All overlay tests (7.1-7.5)
- Video display tests (6.4-6.5)
- Performance tests (9.1-9.4)

### Nice to Have (Enhancement)
- Edge case tests (10.1-10.5)
- Extended runtime (9.5)

---

## Known Issues to Verify

These are logged bugs - verify they still exist:

1. **Video First Frame During Paused Navigation** (Test 5.6)
   - Expected: May not show video first frame
   - Impact: Cosmetic only
   - Status: Known issue, logged for later

---

## Regression Testing

After any code changes, re-run:
1. All automated tests
2. Navigation tests (4.1-4.5)
3. Pause/resume tests (5.1-5.7)
4. Any tests that previously failed

---

## Test Environment

- **OS:** macOS 26.0 (Darwin)
- **Python:** 3.13.7
- **Photos Library:** ~/Pictures/Photos Library.photoslibrary
- **Config:** ~/.photo_slideshow_config.json
- **Cache:** ~/.photo_slideshow_cache/

---

## Reporting Issues

When reporting test failures:

1. **Test ID:** (e.g., Test 4.2)
2. **Expected Result:** (from test plan)
3. **Actual Result:** (what happened)
4. **Steps to Reproduce:** (exact steps)
5. **Logs:** (relevant log entries)
6. **Screenshots/Video:** (if applicable)

---

**Next Steps:**
1. Run automated tests: `./run_tests.sh all`
2. Review results
3. Run manual tests with slideshow
4. Document results
5. Report any failures
