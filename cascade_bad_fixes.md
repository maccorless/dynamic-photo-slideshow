# Cascade Bad Fixes Log

## Purpose
This file tracks failed approaches and fixes that didn't work, so I don't repeat the same mistakes.

---

## FAILED APPROACHES - DO NOT REPEAT

### 1. Timer System Unification (2025-09-25)
**Problem**: Video unpause and nav-while-paused didn't work
**Bad Fix**: Tried to unify photo and video timer systems
**Why It Failed**: 
- Changed working video playback architecture unnecessarily
- Video timer creation happened after video finished playing (wrong sequence)
- Broke basic video functionality to fix isolated pause issue
- Over-engineered solution for simple problem

**Lesson**: Don't change working systems to fix isolated issues
**Correct Approach**: Fix only the specific pause event processing

---

### 2. Video Event Loop Removal (2025-09-25)
**Problem**: Duplicate event handling between video loop and main controller
**Bad Fix**: Removed all event handling from video loop with `pygame.event.clear()`
**Why It Failed**:
- `pygame.event.clear()` discarded all events completely
- Main controller never received key events during video playback
- No key input worked during videos

**Lesson**: Don't remove event handling, redirect it properly
**Correct Approach**: Keep video event handling but call unified controller methods

---

### 3. Timer Creation Sequence Changes (2025-09-25)
**Problem**: Video timer not working with unified system
**Bad Fix**: Tried to change when/how timers are created for videos
**Why It Failed**:
- Video display is blocking call that runs complete playback loop
- Timer created after video finished, not before it started
- Fundamental architecture mismatch

**Lesson**: Blocking video display incompatible with unified timer creation
**Correct Approach**: Keep existing video architecture, fix only pause handling

---

### 4. Countdown System Unification (2025-09-25)
**Problem**: Video countdown showing 0 seconds
**Bad Fix**: Tried to make videos use same countdown system as photos
**Why It Failed**:
- Video playback timing is different from photo timing
- Video has its own event loop that conflicts with photo countdown
- Countdown calculation happened at wrong time in video lifecycle

**Lesson**: Different slide types may need different countdown approaches
**Correct Approach**: Fix video countdown within existing video system

---

## ANTI-PATTERNS TO AVOID

### 1. Architecture Changes for Isolated Issues
- **Don't**: Change entire system architecture to fix one small issue
- **Do**: Make minimal, targeted fixes to the specific problem area

### 2. Unification Without Understanding
- **Don't**: Try to unify systems that work differently for good reasons
- **Do**: Understand why systems are different before attempting unification

### 3. Event Handling Removal
- **Don't**: Remove event handling with `pygame.event.clear()` or similar
- **Do**: Redirect events to appropriate handlers

### 4. Timing/Sequence Changes
- **Don't**: Change the order of operations without understanding dependencies
- **Do**: Trace execution flow before modifying sequences

### 5. Blocking Call Integration
- **Don't**: Try to integrate blocking calls with non-blocking systems
- **Do**: Keep blocking systems separate or make them non-blocking first

---

## DEBUGGING MISTAKES TO AVOID

### 1. Assuming Success Without Log Evidence
- **Don't**: Report fixes as working without seeing expected debug messages
- **Do**: Analyze logs for evidence of functionality before claiming success

### 2. Fixing Symptoms Instead of Root Causes
- **Don't**: Fix the visible problem without understanding why it happens
- **Do**: Trace the root cause through logs and code analysis

### 3. Multiple Changes at Once
- **Don't**: Make multiple architectural changes simultaneously
- **Do**: Make one change at a time with testing between each

---

## SUCCESSFUL PATTERNS TO FOLLOW

### 1. Minimal Targeted Fixes
- Identify the exact problem scope
- Make the smallest possible change to fix it
- Don't touch working systems

### 2. Log-Driven Debugging
- Always analyze logs first to understand the problem
- Look for missing expected debug messages
- Trace execution flow through logs

### 3. Preserve Working Architecture
- If something works, don't change it
- Fix only the broken parts
- Maintain existing patterns and flows

---

## REVIEW CHECKLIST

Before proposing any fix, check:
- [ ] Is this changing a working system to fix an unrelated issue?
- [ ] Am I unifying systems that may be different for good reasons?
- [ ] Am I removing event handling instead of redirecting it?
- [ ] Am I changing timing/sequence without understanding dependencies?
- [ ] Have I analyzed logs to confirm the root cause?
- [ ] Is this the minimal change needed to fix the specific problem?

---

*Last Updated: 2025-09-25*
