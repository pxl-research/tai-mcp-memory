"""
Pytest configuration and shared fixtures for the tai-mcp-memory test suite.
"""

import os

# Must be set before any project module is imported
os.environ["TEST_MODE"] = "1"

import sys
from pathlib import Path

import pytest

project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.backup import invalidate_backup_cache


@pytest.fixture(autouse=True)
def reset_backup_cache():
    """Reset the in-memory backup cache before every test.

    Prevents backup timing state from leaking between tests, which would cause
    should_create_backup() to return stale results based on a previous test's run.
    """
    invalidate_backup_cache()
