"""
Backup utilities for the MCP Memory Server.

Provides automatic backup functionality for the memory database,
including creation, retention management, and timestamp tracking.
"""

import logging
import shutil
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from config import BACKUP_INTERVAL_HOURS, BACKUP_PATH, BACKUP_RETENTION_COUNT, DB_PATH

logger = logging.getLogger(__name__)

# Thread-safe backup tracking
_backup_lock = threading.Lock()
_last_backup_cache: datetime | None = None
_cache_initialized = False


def _parse_backup_timestamp(backup_file: Path) -> datetime | None:
    """Parse timestamp from backup filename.

    Args:
        backup_file: Path to backup file (memory_backup_YYYY-MM-DD_HH-MM-SS.zip)

    Returns:
        datetime object if parsing succeeds, None otherwise
    """
    try:
        timestamp_str = backup_file.stem.replace("memory_backup_", "")
        return datetime.strptime(timestamp_str, "%Y-%m-%d_%H-%M-%S")
    except (ValueError, IndexError):
        logger.warning(f"Skipping backup with invalid filename: {backup_file.name}")
        return None


def get_last_backup_timestamp() -> datetime | None:
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
        timestamp = _parse_backup_timestamp(backup_file)
        if timestamp:
            backup_timestamps.append((timestamp, backup_file))

    if not backup_timestamps:
        return None

    # Return the most recent timestamp
    most_recent = max(backup_timestamps, key=lambda x: x[0])
    return most_recent[0]


def _should_create_backup_unlocked() -> bool:
    """Check if a backup is due. Caller must hold _backup_lock."""
    global _last_backup_cache, _cache_initialized

    if not _cache_initialized:
        _last_backup_cache = get_last_backup_timestamp()
        _cache_initialized = True

    last_backup = _last_backup_cache
    if last_backup is None:
        return True

    time_since_backup = datetime.now() - last_backup
    return time_since_backup >= timedelta(hours=BACKUP_INTERVAL_HOURS)


def _create_backup_unlocked() -> str | None:
    """Create a backup. Caller must hold _backup_lock."""
    global _last_backup_cache

    try:
        backup_dir = Path(BACKUP_PATH)
        backup_dir.mkdir(parents=True, exist_ok=True)

        backup_time = datetime.now()
        timestamp = backup_time.strftime("%Y-%m-%d_%H-%M-%S")
        backup_name = f"memory_backup_{timestamp}"
        backup_path = backup_dir / backup_name

        logger.info(f"Creating backup: {backup_name}.zip")
        shutil.make_archive(str(backup_path), "zip", DB_PATH)

        cleanup_old_backups()

        backup_file = f"{backup_path}.zip"
        _last_backup_cache = backup_time
        logger.info(f"Backup created successfully: {backup_file}")

        return backup_file

    except Exception as e:
        logger.error(f"Failed to create backup: {str(e)}")
        return None


def should_create_backup() -> bool:
    """Check if a backup should be created based on the interval.

    Returns:
        True if a backup should be created, False otherwise.
    """
    with _backup_lock:
        return _should_create_backup_unlocked()


def create_backup() -> str | None:
    """Create a backup of the memory database.

    Creates a timestamped zip archive of the DB_PATH directory containing
    both SQLite and ChromaDB data. Updates the backup cache to prevent
    immediate duplicate backups.

    Returns:
        Path to the created backup file, or None if backup failed.
    """
    with _backup_lock:
        return _create_backup_unlocked()


def create_backup_if_due() -> str | None:
    """Atomically check if a backup is due and create one if so.

    Holds _backup_lock across the check and creation to eliminate the
    TOCTOU race between should_create_backup() and create_backup().

    Returns:
        Path to the created backup file, or None if not due or backup failed.
    """
    with _backup_lock:
        if not _should_create_backup_unlocked():
            return None
        return _create_backup_unlocked()


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
            timestamp = _parse_backup_timestamp(backup_file)
            if timestamp:
                backup_list.append((timestamp, backup_file))

        # Sort by timestamp (newest first)
        backups_sorted = sorted(backup_list, key=lambda x: x[0], reverse=True)

        # Keep only the most recent N backups
        backups_to_delete = backups_sorted[BACKUP_RETENTION_COUNT:]

        for _, backup in backups_to_delete:
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

    backup_list: list[dict[str, Any]] = []
    for backup_file in backup_dir.glob("memory_backup_*.zip"):
        timestamp = _parse_backup_timestamp(backup_file)
        if timestamp:
            stat = backup_file.stat()
            backup_list.append(
                {
                    "timestamp": timestamp,  # For sorting
                    "name": backup_file.name,
                    "path": str(backup_file),
                    "size_mb": round(stat.st_size / (1024 * 1024), 2),
                    "created": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                }
            )

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
