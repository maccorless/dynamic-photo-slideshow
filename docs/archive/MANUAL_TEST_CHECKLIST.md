# Manual Test Checklist

**Date:** _______________  
**Tester:** _______________  
**Commit:** b97d241

Print this page and check off tests as you complete them.

---

## Pre-Test Setup

- [ ] Run automated tests: `./quick_test.sh`
- [ ] All automated tests passed
- [ ] Start slideshow: `./run_slideshow.sh`

---

## 4. Navigation Tests (5 tests)

### Test 4.1: Next Key
- [ ] Press RIGHT arrow
- [ ] Slide advances immediately
- [ ] **Result:** ⬜ Pass | ⬜ Fail
- **Notes:** _________________________________

### Test 4.2: Back Key
- [ ] Advance 3 slides
- [ ] Press LEFT arrow
- [ ] Returns to previous slide
- [ ] **Result:** ⬜ Pass | ⬜ Fail
- **Notes:** _________________________________

### Test 4.3: Multiple Forward
- [ ] Press RIGHT 5 times quickly
- [ ] All 5 advances work
- [ ] **Result:** ⬜ Pass | ⬜ Fail
- **Notes:** _________________________________

### Test 4.4: Multiple Back
- [ ] Advance 5 slides
- [ ] Press LEFT 3 times
- [ ] Goes back 3 slides
- [ ] **Result:** ⬜ Pass | ⬜ Fail
- **Notes:** _________________________________

### Test 4.5: History Boundary
- [ ] Press LEFT at beginning
- [ ] Handles gracefully
- [ ] **Result:** ⬜ Pass | ⬜ Fail
- **Notes:** _________________________________

---

## 5. Pause/Resume Tests (7 tests)

### Test 5.1: Pause Photo
- [ ] Wait 3 seconds on photo
- [ ] Press SPACE
- [ ] Countdown freezes
- [ ] **Result:** ⬜ Pass | ⬜ Fail
- **Notes:** _________________________________

### Test 5.2: Resume Photo
- [ ] Pause photo (5.1)
- [ ] Wait 5 seconds
- [ ] Press SPACE
- [ ] Countdown resumes from paused value
- [ ] **Result:** ⬜ Pass | ⬜ Fail
- **Notes:** _________________________________

### Test 5.3: Pause Video
- [ ] Navigate to video
- [ ] Let video play 2 seconds
- [ ] Press SPACE
- [ ] Video pauses
- [ ] **Result:** ⬜ Pass | ⬜ Fail
- **Notes:** _________________________________

### Test 5.4: Resume Video
- [ ] Pause video (5.3)
- [ ] Wait 3 seconds
- [ ] Press SPACE
- [ ] Video resumes
- [ ] **Result:** ⬜ Pass | ⬜ Fail
- **Notes:** _________________________________

### Test 5.5: Navigate While Paused (Photo)
- [ ] Pause on photo
- [ ] Press RIGHT
- [ ] Advances, stays paused
- [ ] **Result:** ⬜ Pass | ⬜ Fail
- **Notes:** _________________________________

### Test 5.6: Navigate While Paused (Video)
- [ ] Pause on video
- [ ] Press RIGHT
- [ ] Advances to next slide
- [ ] **Result:** ⬜ Pass | ⬜ Fail | ⬜ Known Issue
- **Known Issue:** Video first frame may not show
- **Notes:** _________________________________

### Test 5.7: Unpause After Navigation
- [ ] Pause on photo
- [ ] Navigate forward 2 slides
- [ ] Press SPACE
- [ ] Timer starts from 10s
- [ ] **Result:** ⬜ Pass | ⬜ Fail
- **Notes:** _________________________________

---

## 6. Video Playback Tests (6 tests)

### Test 6.1: Video Auto-Play
- [ ] Navigate to video
- [ ] Video starts automatically
- [ ] **Result:** ⬜ Pass | ⬜ Fail
- **Notes:** _________________________________

### Test 6.2: Video Audio
- [ ] Video with audio plays
- [ ] Audio is clear
- [ ] **Result:** ⬜ Pass | ⬜ Fail
- **Notes:** _________________________________

### Test 6.3: Video Completion
- [ ] Let video play to end
- [ ] Advances automatically
- [ ] **Result:** ⬜ Pass | ⬜ Fail
- **Notes:** _________________________________

### Test 6.4: Portrait Video
- [ ] Navigate to portrait video
- [ ] Displays correctly
- [ ] **Result:** ⬜ Pass | ⬜ Fail
- **Notes:** _________________________________

### Test 6.5: Landscape Video
- [ ] Navigate to landscape video
- [ ] Correct aspect ratio
- [ ] **Result:** ⬜ Pass | ⬜ Fail
- **Notes:** _________________________________

### Test 6.6: Video Overlays
- [ ] Check date overlay
- [ ] Check location overlay
- [ ] Check "Video X/Y" overlay
- [ ] **Result:** ⬜ Pass | ⬜ Fail
- **Notes:** _________________________________

---

## 7. Overlay Tests (5 tests)

### Test 7.1: Date Overlay
- [ ] Check date on photo (bottom left)
- [ ] Format: "Month Day, Year"
- [ ] **Result:** ⬜ Pass | ⬜ Fail
- **Notes:** _________________________________

### Test 7.2: Location Overlay
- [ ] Check location on photo (bottom right)
- [ ] Shows correct location
- [ ] **Result:** ⬜ Pass | ⬜ Fail
- **Notes:** _________________________________

### Test 7.3: No Location
- [ ] Find photo without GPS
- [ ] No location overlay shown
- [ ] **Result:** ⬜ Pass | ⬜ Fail
- **Notes:** _________________________________

### Test 7.4: Video Info
- [ ] Check "Video X/Y" (top left)
- [ ] Shows correct count
- [ ] **Result:** ⬜ Pass | ⬜ Fail
- **Notes:** _________________________________

### Test 7.5: Overlay Readability
- [ ] Navigate through 10 slides
- [ ] All overlays readable
- [ ] **Result:** ⬜ Pass | ⬜ Fail
- **Notes:** _________________________________

---

## 8. Timer Tests (5 tests)

### Test 8.1: Photo Timer
- [ ] Time photo slide
- [ ] Advances after ~10 seconds
- [ ] **Result:** ⬜ Pass | ⬜ Fail
- **Actual:** _______ seconds
- **Notes:** _________________________________

### Test 8.2: Video Timer
- [ ] Time video slide
- [ ] Advances after ~12 seconds
- [ ] **Result:** ⬜ Pass | ⬜ Fail
- **Actual:** _______ seconds
- **Notes:** _________________________________

### Test 8.3: Countdown Display
- [ ] Watch countdown (top right)
- [ ] Counts 10, 9, 8... 1
- [ ] **Result:** ⬜ Pass | ⬜ Fail
- **Notes:** _________________________________

### Test 8.4: Timer on Navigation
- [ ] Wait 5 seconds
- [ ] Press RIGHT
- [ ] New slide starts at 10s
- [ ] **Result:** ⬜ Pass | ⬜ Fail
- **Notes:** _________________________________

### Test 8.5: Timer After Pause
- [ ] Wait 3s (timer at 7)
- [ ] Pause
- [ ] Wait 5s
- [ ] Resume
- [ ] Timer resumes at 7
- [ ] **Result:** ⬜ Pass | ⬜ Fail
- **Notes:** _________________________________

---

## Summary

**Total Tests:** 33  
**Passed:** _______  
**Failed:** _______  
**Known Issues:** _______

### Critical Tests (Must Pass)
- [ ] All navigation tests (4.1-4.5)
- [ ] All pause/resume tests (5.1-5.7)
- [ ] Video playback (6.1-6.3)
- [ ] Timer accuracy (8.1-8.4)

### Pass Criteria
- **Release Ready:** All critical tests pass
- **Minor Issues:** < 3 non-critical failures
- **Needs Work:** > 3 failures or any critical failure

### Overall Assessment
⬜ **PASS** - Ready for use  
⬜ **CONDITIONAL** - Minor issues, usable  
⬜ **FAIL** - Needs fixes before use

---

## Notes / Issues Found

_____________________________________________

_____________________________________________

_____________________________________________

_____________________________________________

_____________________________________________

---

## Next Steps After Testing

If all tests pass:
1. [ ] Install video automation: `cd utilities && ./setup_daily_download.sh install`
2. [ ] Verify automation: `./setup_daily_download.sh status`
3. [ ] Update PROJECT_STATUS.md with results
4. [ ] System ready for daily use!

If tests fail:
1. [ ] Document failures in detail
2. [ ] Check logs in `~/.photo_slideshow_cache/logs/`
3. [ ] Report issues with test IDs
4. [ ] Review TEST_PLAN.md for troubleshooting
