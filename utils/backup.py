"""
Backup utilities for the MCP Memory Server.

Provides automatic backup functionality for the memory database,
including creation, retention management, and timestamp tracking.
"""

import os
import shutil
import logging
import threading
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

from config import DB_PATH, BACKUP_PATH, BACKUP_INTERVAL_HOURS, BACKUP_RETENTION_COUNT

logger = logging.getLogger(__name__)

# Thread-safe backup tracking
_backup_lock = threading.Lock()
_last_backup_cache: Optional[datetime] = None
_cache_initialized = False


def get_last_backup_timestamp() -> Optional[datetime]:
    """Get the timestamp of the most recent backup from filename.

    Parses timestamps from backup filenames (memory_backup_YYYY-MM-DD_HH-MM-SS.zip)
    instead of relying on file modification times, which can be unreliable.

    Returns:
        datetime object of the most recent backup, or None if no backups exist.
    """
    backup_dir = Path(BACKUP_PATH)
    if not backup_dir.exists():
        return None

    backups = list(backup_dir.glob("memory_backup_*.zip"))
    if not backups:
        return None

    # Parse timestamps from filenames
    backup_timestamps = []
    for backup_file in backups:
        try:
            # Extract: memory_backup_2026-01-29_16-24-55.zip → 2026-01-29_16-24-55
            timestamp_str = backup_file.stem.replace('memory_backup_', '')
            timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d_%H-%M-%S')
            backup_timestamps.append((timestamp, backup_file))
        except (ValueError, IndexError) as e:
            logger.warning(f"Skipping backup with invalid filename: {backup_file.name}")
            continue

    if not backup_timestamps:
        return None

    # Return the most recent timestamp
    most_recent = max(backup_timestamps, key=lambda x: x[0])
    return most_recent[0]


def should_create_backup() -> bool:
    """Check if a backup should be created based on the interval.

    Uses thread-safe caching to prevent race conditions during concurrent
    store_memory() calls. Cache is initialized on first call and updated
    after each backup.

    Returns:
        True if a backup should be created, False otherwise.
    """
    global _last_backup_cache, _cache_initialized

    with _backup_lock:
        # Initialize cache on first call
        if not _cache_initialized:
            _last_backup_cache = get_last_backup_timestamp()
            _cache_initialized = True

        last_backup = _last_backup_cache

        # If no backup exists, create one
        if last_backup is None:
            return True

        # Check if enough time has passed
        time_since_backup = datetime.now() - last_backup
        interval = timedelta(hours=BACKUP_INTERVAL_HOURS)

        return time_since_backup >= interval


def create_backup() -> Optional[str]:
    """Create a backup of the memory database.

    Creates a timestamped zip archive of the DB_PATH directory containing
    both SQLite and ChromaDB data. Updates the backup cache to prevent
    immediate duplicate backups.

    Returns:
        Path to the created backup file, or None if backup failed.
    """
    global _last_backup_cache

    with _backup_lock:  # Prevent concurrent backup creation
        try:
            # Ensure backup directory exists
            backup_dir = Path(BACKUP_PATH)
            backup_dir.mkdir(parents=True, exist_ok=True)

            # Create timestamped backup filename
            backup_time = datetime.now()
            timestamp = backup_time.strftime("%Y-%m-%d_%H-%M-%S")
            backup_name = f"memory_backup_{timestamp}"
            backup_path = backup_dir / backup_name

            # Create the zip archive
            logger.info(f"Creating backup: {backup_name}.zip")
            shutil.make_archive(str(backup_path), 'zip', DB_PATH)

            # Cleanup old backups
            cleanup_old_backups()

            backup_file = f"{backup_path}.zip"

            # Update cache with the timestamp from the filename we just created
            _last_backup_cache = backup_time
            logger.info(f"Backup created successfully: {backup_file}")

            return backup_file

        except Exception as e:
            logger.error(f"Failed to create backup: {str(e)}")
            return None


def cleanup_old_backups() -> None:
    """Remove old backups, keeping only the most recent N backups.

    Sorts backups by timestamp parsed from filename rather than modification time.
    Retention count is configured via BACKUP_RETENTION_COUNT.
    """
    try:
        backup_dir = Path(BACKUP_PATH)
        if not backup_dir.exists():
            return

        # Get all backup files with parsed timestamps
        backup_list = []
        for backup_file in backup_dir.glob("memory_backup_*.zip"):
            try:
                timestamp_str = backup_file.stem.replace('memory_backup_', '')
                timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d_%H-%M-%S')
                backup_list.append((timestamp, backup_file))
            except (ValueError, IndexError):
                logger.warning(f"Skipping backup with invalid filename: {backup_file.name}")
                continue

        # Sort by timestamp (newest first)
        backups_sorted = sorted(backup_list, key=lambda x: x[0], reverse=True)

        # Keep only the most recent N backups
        backups_to_delete = backups_sorted[BACKUP_RETENTION_COUNT:]

        for timestamp, backup in backups_to_delete:
            logger.info(f"Deleting old backup: {backup.name}")
            backup.unlink()

    except Exception as e:
        logger.error(f"Failed to cleanup old backups: {str(e)}")


def list_backups() -> list:
    """List all available backups with their details.

    Returns:
        List of dicts containing backup information (name, size, date).
        Sorted by parsed filename timestamp (newest first).
    """
    backup_dir = Path(BACKUP_PATH)
    if not backup_dir.exists():
        return []

    backup_list = []
    for backup_file in backup_dir.glob("memory_backup_*.zip"):
        try:
            # Parse timestamp from filename
            timestamp_str = backup_file.stem.replace('memory_backup_', '')
            timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d_%H-%M-%S')

            stat = backup_file.stat()
            backup_list.append({
                "timestamp": timestamp,  # For sorting
                "name": backup_file.name,
                "path": str(backup_file),
                "size_mb": round(stat.st_size / (1024 * 1024), 2),
                "created": timestamp.strftime("%Y-%m-%d %H:%M:%S")
            })
        except (ValueError, IndexError):
            logger.warning(f"Skipping backup with invalid filename: {backup_file.name}")
            continue

    # Sort by timestamp (newest first)
    backup_list.sort(key=lambda x: x["timestamp"], reverse=True)

    # Remove timestamp field used only for sorting
    for backup in backup_list:
        del backup["timestamp"]

    return backup_list


def invalidate_backup_cache() -> None:
    """Invalidate the backup timestamp cache.

    Forces the next call to should_create_backup() to re-read from filesystem.
    Useful for testing or manual cache invalidation scenarios.
    """
    global _last_backup_cache, _cache_initialized

    with _backup_lock:
        _last_backup_cache = None
        _cache_initialized = False
        logger.info("Backup cache invalidated")
