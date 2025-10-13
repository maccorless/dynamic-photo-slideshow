#!/usr/bin/env python3
"""
Automated Countdown Thread Log Analyzer

Parses slideshow logs to identify multiple countdown thread issues.
"""

import re
import sys
from collections import defaultdict
from datetime import datetime

def parse_timestamp(line):
    """Extract timestamp from log line."""
    match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})', line)
    if match:
        return match.group(1)
    return None

def parse_manager_id(line):
    """Extract manager ID from log line."""
    match = re.search(r'MGR-(\d+)', line)
    if match:
        return f"MGR-{match.group(1)}"
    return None

def parse_thread_id(line):
    """Extract thread ID from log line."""
    match = re.search(r'thread_id=(\d+)', line)
    if match:
        return match.group(1)
    return None

def analyze_log_file(log_path):
    """Analyze countdown log for threading issues."""
    
    print("=" * 80)
    print("COUNTDOWN THREAD ANALYSIS")
    print("=" * 80)
    print()
    
    # Track manager lifecycle
    managers = {}  # manager_id -> {created, started_countdown, finished, thread_id}
    active_threads = {}  # thread_id -> [timestamps of activity]
    cleanup_events = []
    create_events = []
    overlaps = []
    
    with open(log_path, 'r') as f:
        lines = f.readlines()
    
    print(f"Processing {len(lines)} lines...")
    print()
    
    # Parse log lines
    for line in lines:
        timestamp = parse_timestamp(line)
        manager_id = parse_manager_id(line)
        thread_id = parse_thread_id(line)
        
        # Track manager creation
        if 'Timer manager instance created' in line and manager_id:
            managers[manager_id] = {
                'created': timestamp,
                'started_countdown': None,
                'finished': None,
                'thread_id': None
            }
            create_events.append((timestamp, manager_id))
        
        # Track countdown worker start
        if 'Countdown worker started' in line and manager_id and thread_id:
            if manager_id in managers:
                managers[manager_id]['started_countdown'] = timestamp
                managers[manager_id]['thread_id'] = thread_id
                if thread_id not in active_threads:
                    active_threads[thread_id] = []
                active_threads[thread_id].append(('START', timestamp, manager_id))
        
        # Track countdown worker finish
        if 'Countdown worker finished' in line and manager_id and thread_id:
            if manager_id in managers:
                managers[manager_id]['finished'] = timestamp
                if thread_id in active_threads:
                    active_threads[thread_id].append(('FINISH', timestamp, manager_id))
        
        # Track countdown iterations (activity)
        if 'Countdown iteration' in line and manager_id and thread_id:
            if thread_id in active_threads:
                active_threads[thread_id].append(('ACTIVE', timestamp, manager_id))
        
        # Track cleanup events
        if 'CLEANUP-START' in line:
            cleanup_events.append(('START', timestamp, line))
        if 'CLEANUP-COMPLETE' in line:
            cleanup_events.append(('COMPLETE', timestamp, line))
        if 'CLEANUP-DETAIL' in line and manager_id:
            cleanup_events.append(('DETAIL', timestamp, manager_id))
    
    # Analysis 1: Find overlapping countdown threads
    print("=" * 80)
    print("ANALYSIS 1: OVERLAPPING COUNTDOWN THREADS")
    print("=" * 80)
    print()
    
    # For each timestamp, check how many threads were active
    all_timestamps = []
    for thread_id, events in active_threads.items():
        for event_type, timestamp, manager_id in events:
            all_timestamps.append((timestamp, event_type, thread_id, manager_id))
    
    all_timestamps.sort()
    
    # Track active threads over time
    currently_active = set()
    overlap_windows = []
    
    for timestamp, event_type, thread_id, manager_id in all_timestamps:
        if event_type == 'START':
            currently_active.add((thread_id, manager_id))
        elif event_type == 'FINISH':
            currently_active.discard((thread_id, manager_id))
        
        if len(currently_active) > 1:
            overlap_windows.append((timestamp, list(currently_active)))
    
    if overlap_windows:
        print(f"⚠️  FOUND {len(overlap_windows)} INSTANCES OF MULTIPLE COUNTDOWN THREADS RUNNING!")
        print()
        
        # Show first 10 overlaps
        for i, (timestamp, active) in enumerate(overlap_windows[:10]):
            print(f"Overlap {i+1} at {timestamp}:")
            for thread_id, manager_id in active:
                print(f"  - Thread {thread_id} ({manager_id})")
        
        if len(overlap_windows) > 10:
            print(f"  ... and {len(overlap_windows) - 10} more overlaps")
        print()
    else:
        print("✅ No overlapping countdown threads detected!")
        print()
    
    # Analysis 2: Check cleanup timing
    print("=" * 80)
    print("ANALYSIS 2: CLEANUP vs CREATE TIMING")
    print("=" * 80)
    print()
    
    # Find cases where managers are created before previous cleanup completes
    timing_issues = []
    for i, (create_time, manager_id) in enumerate(create_events):
        # Find cleanup events around this time
        recent_cleanups = [e for e in cleanup_events if e[0] in ['START', 'COMPLETE']]
        
        # Check if there's an ongoing cleanup
        for j, (event_type, cleanup_time, _) in enumerate(recent_cleanups):
            if event_type == 'START' and cleanup_time <= create_time:
                # Look for matching COMPLETE
                for k in range(j+1, len(recent_cleanups)):
                    if recent_cleanups[k][0] == 'COMPLETE':
                        complete_time = recent_cleanups[k][1]
                        if complete_time > create_time:
                            timing_issues.append({
                                'manager': manager_id,
                                'cleanup_start': cleanup_time,
                                'create_time': create_time,
                                'cleanup_complete': complete_time
                            })
                        break
    
    if timing_issues:
        print(f"⚠️  FOUND {len(timing_issues)} CASES WHERE NEW MANAGER CREATED DURING CLEANUP!")
        print()
        for issue in timing_issues[:5]:
            print(f"Manager {issue['manager']}:")
            print(f"  Cleanup started:  {issue['cleanup_start']}")
            print(f"  Manager created:  {issue['create_time']} ⚠️ DURING CLEANUP")
            print(f"  Cleanup finished: {issue['cleanup_complete']}")
            print()
    else:
        print("✅ All managers created after cleanup completed!")
        print()
    
    # Analysis 3: Manager lifecycle summary
    print("=" * 80)
    print("ANALYSIS 3: MANAGER LIFECYCLE SUMMARY")
    print("=" * 80)
    print()
    
    print(f"Total managers created: {len(managers)}")
    
    orphaned = []
    for manager_id, info in managers.items():
        if info['started_countdown'] and not info['finished']:
            orphaned.append(manager_id)
    
    if orphaned:
        print(f"⚠️  {len(orphaned)} orphaned managers (started countdown but never finished):")
        for mgr in orphaned[:5]:
            print(f"  - {mgr}")
    else:
        print("✅ All managers that started countdown also finished!")
    
    print()
    
    # Analysis 4: Thread reuse
    print("=" * 80)
    print("ANALYSIS 4: THREAD REUSE PATTERNS")
    print("=" * 80)
    print()
    
    thread_usage = defaultdict(list)
    for manager_id, info in managers.items():
        if info['thread_id']:
            thread_usage[info['thread_id']].append(manager_id)
    
    print(f"Unique threads used: {len(thread_usage)}")
    
    reused_threads = {tid: mgrs for tid, mgrs in thread_usage.items() if len(mgrs) > 1}
    if reused_threads:
        print(f"Threads reused by multiple managers: {len(reused_threads)}")
        for tid, mgrs in list(reused_threads.items())[:5]:
            print(f"  Thread {tid}: {', '.join(mgrs)}")
    else:
        print("No thread reuse (each manager gets new thread)")
    
    print()
    
    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()
    
    issues_found = 0
    if overlap_windows:
        print(f"❌ ISSUE: {len(overlap_windows)} instances of overlapping countdown threads")
        issues_found += 1
    if timing_issues:
        print(f"❌ ISSUE: {len(timing_issues)} managers created during cleanup")
        issues_found += 1
    if orphaned:
        print(f"⚠️  WARNING: {len(orphaned)} orphaned managers")
        issues_found += 1
    
    if issues_found == 0:
        print("✅ No issues detected! Countdown threading is working correctly.")
    else:
        print()
        print(f"Total issues found: {issues_found}")
    
    print()
    return issues_found

if __name__ == '__main__':
    if len(sys.argv) > 1:
        log_file = sys.argv[1]
    else:
        log_file = 'countdown_test.log'
    
    try:
        analyze_log_file(log_file)
    except FileNotFoundError:
        print(f"Error: Log file '{log_file}' not found!")
        print()
        print("Usage:")
        print(f"  {sys.argv[0]} [log_file]")
        print()
        print("Default log file: countdown_test.log")
        sys.exit(1)
    except Exception as e:
        print(f"Error analyzing log: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
