"""
Test script for backup race condition fix.

This script simulates rapid concurrent store_memory() operations to verify
that the backup system no longer creates duplicate backups.
"""

# Enable test mode to use separate test database
import os
os.environ['TEST_MODE'] = '1'

import sys
import time
import threading
from pathlib import Path
import shutil

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from config import BACKUP_PATH, DB_PATH
from utils.backup import (
    get_last_backup_timestamp,
    should_create_backup,
    create_backup,
    invalidate_backup_cache,
    list_backups
)


def test_race_condition_prevention():
    """Test that rapid concurrent checks don't create duplicate backups."""
    print("=" * 60)
    print("Testing Race Condition Prevention")
    print("=" * 60)
    print()

    # Ensure clean test environment
    backup_dir = Path(BACKUP_PATH)
    if backup_dir.exists():
        print(f"Cleaning up existing backups in {BACKUP_PATH}")
        shutil.rmtree(backup_dir)
        print()

    # Invalidate cache to start fresh
    invalidate_backup_cache()

    print("Test 1: Rapid sequential checks (should only create 1 backup)")
    print("-" * 60)

    results = []
    for i in range(10):
        if should_create_backup():
            backup_file = create_backup()
            results.append(backup_file)
            print(f"  Check {i+1}: Created backup: {Path(backup_file).name}")
        else:
            print(f"  Check {i+1}: No backup needed (within interval)")

    assert len(results) == 1, f"Expected 1 backup, but created {len(results)}"
    print(f"\n✓ Passed: Only 1 backup created from 10 rapid checks")
    print()

    # Clean up for next test
    if backup_dir.exists():
        shutil.rmtree(backup_dir)
    invalidate_backup_cache()

    print("Test 2: Concurrent thread checks (should only create 1 backup)")
    print("-" * 60)

    thread_results = []
    lock = threading.Lock()

    def check_and_backup(thread_id):
        """Thread worker that checks and creates backup if needed."""
        if should_create_backup():
            backup_file = create_backup()
            with lock:
                thread_results.append((thread_id, backup_file))
                print(f"  Thread {thread_id}: Created backup")
        else:
            print(f"  Thread {thread_id}: No backup needed")

    # Launch 5 concurrent threads
    threads = []
    for i in range(5):
        thread = threading.Thread(target=check_and_backup, args=(i+1,))
        threads.append(thread)
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    assert len(thread_results) == 1, f"Expected 1 backup, but created {len(thread_results)}"
    print(f"\n✓ Passed: Only 1 backup created from 5 concurrent threads")
    print()

    print("Test 3: Verify backup timestamp parsing works correctly")
    print("-" * 60)

    # Get the timestamp from the created backup
    last_backup = get_last_backup_timestamp()
    assert last_backup is not None, "Should have a backup timestamp"

    # List backups and verify timestamp matches
    backups = list_backups()
    assert len(backups) == 1, f"Expected 1 backup, found {len(backups)}"

    # Parse timestamp from backup name
    backup_name = backups[0]['name']
    timestamp_str = backup_name.replace('memory_backup_', '').replace('.zip', '')

    print(f"  Backup name: {backup_name}")
    print(f"  Parsed timestamp: {last_backup}")
    print(f"  Created field: {backups[0]['created']}")

    # Verify the parsed timestamp matches the created field
    assert backups[0]['created'] == last_backup.strftime("%Y-%m-%d %H:%M:%S"), \
        "Timestamp parsing mismatch"

    print(f"\n✓ Passed: Timestamp parsing works correctly")
    print()

    print("Test 4: Cache invalidation allows new timestamp check")
    print("-" * 60)

    # First check should not create backup (within interval)
    should_backup = should_create_backup()
    assert should_backup is False, "Should not create backup within interval"
    print(f"  Before invalidation: should_create_backup() = {should_backup}")

    # Invalidate cache
    invalidate_backup_cache()
    print(f"  Cache invalidated")

    # After invalidation, it should re-read from filesystem
    # (still within interval, so should be False)
    should_backup = should_create_backup()
    assert should_backup is False, "Should still not create backup within interval"
    print(f"  After invalidation: should_create_backup() = {should_backup}")

    print(f"\n✓ Passed: Cache invalidation works correctly")
    print()

    print("=" * 60)
    print("All race condition tests passed!")
    print("=" * 60)
    print()


def test_rapid_operations_simulation():
    """Simulate the original problem: rapid store operations."""
    print("=" * 60)
    print("Simulating Original Problem: Rapid Operations")
    print("=" * 60)
    print()

    # Ensure clean test environment
    backup_dir = Path(BACKUP_PATH)
    if backup_dir.exists():
        shutil.rmtree(backup_dir)
    invalidate_backup_cache()

    print("Simulating 3 rapid store_memory() calls within 3 seconds...")
    print("-" * 60)

    backup_count = 0
    for i in range(3):
        print(f"\nOperation {i+1}:")

        # Simulate what happens in store_memory()
        if should_create_backup():
            backup_file = create_backup()
            backup_count += 1
            print(f"  ✓ Backup created: {Path(backup_file).name}")
        else:
            print(f"  ✓ Backup skipped (within interval)")

        # Small delay like the original problem
        if i < 2:
            time.sleep(1)

    print()
    print("-" * 60)
    print(f"Result: {backup_count} backup(s) created")

    # List all backups to verify
    backups = list_backups()
    print(f"Backups found: {len(backups)}")
    for backup in backups:
        print(f"  - {backup['name']}")

    assert backup_count == 1, f"Expected 1 backup, but created {backup_count}"
    assert len(backups) == 1, f"Expected 1 backup file, but found {len(backups)}"

    print()
    print("✓ Passed: Race condition is fixed!")
    print("  (Original problem would have created 3 backups)")
    print()

    print("=" * 60)
    print("Simulation test passed!")
    print("=" * 60)
    print()


def main():
    """Run all race condition tests."""
    try:
        # Test race condition prevention
        test_race_condition_prevention()

        # Simulate original problem
        test_rapid_operations_simulation()

        print()
        print("=" * 60)
        print("ALL RACE CONDITION TESTS PASSED!")
        print("=" * 60)

    except Exception as e:
        print()
        print("=" * 60)
        print("TEST FAILED!")
        print("=" * 60)
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
