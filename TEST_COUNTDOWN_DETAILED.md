# Detailed Countdown Thread Testing Instructions

**Date:** October 13, 2025  
**Purpose:** Diagnose erratic countdown behavior during rapid navigation

---

## Enhanced Debugging Added

I've added comprehensive logging to track:
1. **Manager ID:** Each timer manager gets unique ID (e.g., MGR-1234)
2. **Thread ID:** Each countdown thread's unique identifier
3. **Iteration count:** How many times each thread loops
4. **Active state:** Whether thread thinks it should be running
5. **Timing:** When threads start, loop, and finish

---

## Test Instructions

### Step 1: Run Rapid Navigation Test

```bash
cd /Users/ken/CascadeProjects/photo-slideshow

# Start slideshow and save complete logs
./slideshow_env/bin/python main_pygame.py 2>&1 | tee countdown_test.log
```

### Step 2: Perform Test Actions

**Once slideshow starts:**
1. Wait for **first slide to appear** (2-3 seconds)
2. Press **RIGHT arrow 10 times rapidly** (as fast as you can)
3. Watch the countdown number in top-right corner
4. Note if it jumps (e.g., 8, 7, 9, 6, 8, 5...)
5. Wait 2 seconds
6. Press **ESC** to exit

### Step 3: Save and Share Logs

The complete logs are saved to `countdown_test.log`

**Send me the entire log file or at least these sections:**

```bash
# Extract just the countdown-related logs
grep -E "TIMER-MGR|COUNTDOWN" countdown_test.log > countdown_analysis.log
cat countdown_analysis.log
```

---

## What to Look For in Logs

### ✅ Good Pattern (Working)

```
[TIMER-MGR-1234] Timer manager instance created
[TIMER-MGR-1234] Started countdown display thread: Thread-1, id=123456
[TIMER-MGR-1234] Countdown worker started, thread_id=123456
[TIMER-MGR-1234] Countdown iteration 1, remaining=9.0s, is_active=True, thread_id=123456
[COUNTDOWN-DISPLAY] MGR-1234 Thread-123456: show_countdown(9s) called

[Navigation happens]

[TIMER-MGR] Stopping countdown thread, waiting for it to finish...
[TIMER-MGR-1234] Countdown worker exiting: remaining=8.0s, is_active=False
[TIMER-MGR-1234] Countdown worker finished, thread_id=123456
[TIMER-MGR] Countdown thread stopped successfully

[New slide]

[TIMER-MGR-5678] Timer manager instance created
[TIMER-MGR-5678] Started countdown display thread: Thread-2, id=789012
[TIMER-MGR-5678] Countdown worker started, thread_id=789012
```

**Key:** Old thread (123456) finishes BEFORE new thread (789012) starts

### ❌ Bad Pattern (Multiple Threads)

```
[TIMER-MGR-1234] Countdown iteration 3, remaining=7.0s, thread_id=123456
[COUNTDOWN-DISPLAY] MGR-1234 Thread-123456: show_countdown(7s) called

[Navigation happens]

[TIMER-MGR-5678] Countdown iteration 1, remaining=9.0s, thread_id=789012
[COUNTDOWN-DISPLAY] MGR-5678 Thread-789012: show_countdown(9s) called

[OLD THREAD STILL RUNNING!]
[TIMER-MGR-1234] Countdown iteration 4, remaining=6.0s, thread_id=123456
[COUNTDOWN-DISPLAY] MGR-1234 Thread-123456: show_countdown(6s) called
```

**Problem:** Both thread 123456 AND 789012 calling show_countdown()

---

## Analysis Questions

From the logs, we'll be able to answer:

1. **Are multiple threads calling show_countdown() simultaneously?**
   - Look for different thread IDs at the same time
   
2. **How long does thread.join() actually wait?**
   - Check time between "Stopping countdown thread" and "stopped successfully"
   
3. **Does the old thread exit promptly?**
   - Check if "Countdown worker finished" appears right after is_active=False
   
4. **Are threads from different managers overlapping?**
   - Check if MGR-1234 is still logging after MGR-5678 starts

---

## Quick Analysis Command

After the test, run this to see the thread lifecycle:

```bash
# Show all timer manager lifecycle events
grep "Timer manager instance created\|Countdown worker started\|Countdown worker finished" countdown_test.log

# Show countdown calls with timestamps
grep "COUNTDOWN-DISPLAY.*show_countdown" countdown_test.log | head -50

# Count how many threads were created
grep "Countdown worker started" countdown_test.log | wc -l

# Count how many threads finished
grep "Countdown worker finished" countdown_test.log | wc -l
```

---

## Expected Results

**If fix is working:**
- Each "Countdown worker finished" appears BEFORE next "Timer manager instance created"
- No overlap of countdown calls from different MGR-IDs
- Smooth countdown in UI (10, 9, 8, 7...)

**If still broken:**
- Multiple MGR-IDs calling show_countdown() at same time
- "Countdown worker finished" appears AFTER new manager starts
- Jumping countdown in UI (8, 7, 9, 6...)

---

## Ready to Test

1. Start the slideshow with logging: `./slideshow_env/bin/python main_pygame.py 2>&1 | tee countdown_test.log`
2. Do rapid navigation (10x RIGHT arrow)
3. Exit (ESC)
4. Share the countdown_test.log or countdown_analysis.log

The enhanced logging will show us exactly what's happening with the threads!
