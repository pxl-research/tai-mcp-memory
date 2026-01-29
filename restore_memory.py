#!/usr/bin/env python3
"""
Standalone script to restore memory database from a backup.

This script allows users to restore their memory database from a previous backup.
It includes safety checks and creates a backup of the current database before
restoring to prevent data loss.

Usage:
    python restore_memory.py
    python restore_memory.py --file backups/memory_backup_2026-01-29_14-30-00.zip
"""

import os
import sys
import shutil
import zipfile
from pathlib import Path
from datetime import datetime
import argparse

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from config import DB_PATH, BACKUP_PATH
from utils.backup import list_backups


def create_safety_backup() -> str:
    """Create a safety backup of the current database before restoring.

    Returns:
        Path to the safety backup file.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    safety_backup_name = f"safety_backup_{timestamp}"
    safety_backup_path = Path(BACKUP_PATH) / safety_backup_name

    # Ensure backup directory exists
    Path(BACKUP_PATH).mkdir(parents=True, exist_ok=True)

    # Create the zip archive
    shutil.make_archive(str(safety_backup_path), 'zip', DB_PATH)

    return f"{safety_backup_path}.zip"


def restore_backup(backup_file: str) -> bool:
    """Restore database from a backup file.

    Args:
        backup_file: Path to the backup zip file.

    Returns:
        True if restore was successful, False otherwise.
    """
    try:
        backup_path = Path(backup_file)
        if not backup_path.exists():
            print(f"Error: Backup file not found: {backup_file}")
            return False

        # Remove current database
        db_path = Path(DB_PATH)
        if db_path.exists():
            print(f"Removing current database: {DB_PATH}")
            shutil.rmtree(db_path)

        # Extract backup
        print(f"Extracting backup: {backup_file}")
        db_path.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(backup_path, 'r') as zip_ref:
            zip_ref.extractall(db_path)

        print("Restore completed successfully!")
        return True

    except Exception as e:
        print(f"Error during restore: {str(e)}")
        return False


def main():
    """Main entry point for the restore script."""
    parser = argparse.ArgumentParser(description="Restore memory database from backup")
    parser.add_argument(
        "--file",
        type=str,
        help="Path to the backup file to restore"
    )
    args = parser.parse_args()

    print("=" * 60)
    print("Memory Database Restore Utility")
    print("=" * 60)
    print()

    # List available backups
    backups = list_backups()

    if not backups and not args.file:
        print("No backups found in the backup directory.")
        print(f"Backup directory: {BACKUP_PATH}")
        sys.exit(1)

    # If backup file specified via command line
    if args.file:
        backup_file = args.file
        print(f"Selected backup: {backup_file}")
    else:
        # Interactive selection
        print(f"Available backups ({len(backups)} found):")
        print()
        for idx, backup in enumerate(backups, 1):
            print(f"  [{idx}] {backup['name']}")
            print(f"      Created: {backup['created']}")
            print(f"      Size: {backup['size_mb']} MB")
            print()

        # Prompt for selection
        try:
            selection = input(f"Select backup to restore [1-{len(backups)}] or 'q' to quit: ").strip()
            if selection.lower() == 'q':
                print("Restore cancelled.")
                sys.exit(0)

            idx = int(selection) - 1
            if idx < 0 or idx >= len(backups):
                print("Invalid selection.")
                sys.exit(1)

            backup_file = backups[idx]['path']
        except (ValueError, KeyboardInterrupt):
            print("\nRestore cancelled.")
            sys.exit(1)

    # Warning and confirmation
    print()
    print("!" * 60)
    print("WARNING: This operation will REPLACE your current database!")
    print("!" * 60)
    print()
    print("A safety backup of your current database will be created")
    print("before restoration begins.")
    print()

    try:
        confirm = input("Type 'yes' to proceed with restore: ").strip().lower()
        if confirm != 'yes':
            print("Restore cancelled.")
            sys.exit(0)
    except KeyboardInterrupt:
        print("\nRestore cancelled.")
        sys.exit(1)

    # Create safety backup
    print()
    print("Creating safety backup of current database...")
    try:
        safety_backup = create_safety_backup()
        print(f"Safety backup created: {safety_backup}")
    except Exception as e:
        print(f"Error creating safety backup: {str(e)}")
        print("Restore aborted to prevent data loss.")
        sys.exit(1)

    # Perform restore
    print()
    success = restore_backup(backup_file)

    if success:
        print()
        print("=" * 60)
        print("Restore completed successfully!")
        print("=" * 60)
        print()
        print("Your memory database has been restored.")
        print(f"Safety backup is available at: {safety_backup}")
        print()
        print("You may need to restart the MCP server for changes to take effect.")
    else:
        print()
        print("=" * 60)
        print("Restore failed!")
        print("=" * 60)
        print()
        print(f"Your original database is backed up at: {safety_backup}")
        sys.exit(1)


if __name__ == "__main__":
    main()
