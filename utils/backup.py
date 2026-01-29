"""
Backup utilities for the MCP Memory Server.

Provides automatic backup functionality for the memory database,
including creation, retention management, and timestamp tracking.
"""

import os
import shutil
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

from config import DB_PATH, BACKUP_PATH, BACKUP_INTERVAL_HOURS, BACKUP_RETENTION_COUNT

logger = logging.getLogger(__name__)


def get_last_backup_timestamp() -> Optional[datetime]:
    """Get the timestamp of the most recent backup.

    Returns:
        datetime object of the most recent backup, or None if no backups exist.
    """
    backup_dir = Path(BACKUP_PATH)
    if not backup_dir.exists():
        return None

    # List all backup files
    backups = list(backup_dir.glob("memory_backup_*.zip"))
    if not backups:
        return None

    # Get the most recent backup by modification time
    most_recent = max(backups, key=lambda p: p.stat().st_mtime)
    return datetime.fromtimestamp(most_recent.stat().st_mtime)


def should_create_backup() -> bool:
    """Check if a backup should be created based on the interval.

    Returns:
        True if a backup should be created, False otherwise.
    """
    last_backup = get_last_backup_timestamp()

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
    both SQLite and ChromaDB data.

    Returns:
        Path to the created backup file, or None if backup failed.
    """
    try:
        # Ensure backup directory exists
        backup_dir = Path(BACKUP_PATH)
        backup_dir.mkdir(parents=True, exist_ok=True)

        # Create timestamped backup filename
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_name = f"memory_backup_{timestamp}"
        backup_path = backup_dir / backup_name

        # Create the zip archive
        logger.info(f"Creating backup: {backup_name}.zip")
        shutil.make_archive(str(backup_path), 'zip', DB_PATH)

        # Cleanup old backups
        cleanup_old_backups()

        backup_file = f"{backup_path}.zip"
        logger.info(f"Backup created successfully: {backup_file}")
        return backup_file

    except Exception as e:
        logger.error(f"Failed to create backup: {str(e)}")
        return None


def cleanup_old_backups() -> None:
    """Remove old backups, keeping only the most recent N backups.

    Retention count is configured via BACKUP_RETENTION_COUNT.
    """
    try:
        backup_dir = Path(BACKUP_PATH)
        if not backup_dir.exists():
            return

        # Get all backup files sorted by modification time (newest first)
        backups = sorted(
            backup_dir.glob("memory_backup_*.zip"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )

        # Keep only the most recent N backups
        backups_to_delete = backups[BACKUP_RETENTION_COUNT:]

        for backup in backups_to_delete:
            logger.info(f"Deleting old backup: {backup.name}")
            backup.unlink()

    except Exception as e:
        logger.error(f"Failed to cleanup old backups: {str(e)}")


def list_backups() -> list:
    """List all available backups with their details.

    Returns:
        List of dicts containing backup information (name, size, date).
    """
    backup_dir = Path(BACKUP_PATH)
    if not backup_dir.exists():
        return []

    backups = []
    for backup_file in sorted(
        backup_dir.glob("memory_backup_*.zip"),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    ):
        stat = backup_file.stat()
        backups.append({
            "name": backup_file.name,
            "path": str(backup_file),
            "size_mb": round(stat.st_size / (1024 * 1024), 2),
            "created": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        })

    return backups
