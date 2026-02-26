"""
Configuration settings for the MCP Memory Server.
"""

import os

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Check for test mode
_TEST_MODE = os.getenv("TEST_MODE", "0") == "1"

# Database paths
if _TEST_MODE:
    DB_PATH = "./test_db"
else:
    DB_PATH = os.getenv("DB_PATH", "./memory_db")

SQLITE_PATH = os.path.join(DB_PATH, "memory.sqlite")
CHROMA_PATH = os.path.join(DB_PATH, "chroma")

# Collection names
MEMORY_COLLECTION = "memory_items"
TOPICS_COLLECTION = "topics"
SUMMARY_COLLECTION = "summaries"

# OpenRouter API settings
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_ENDPOINT = os.getenv("OPENROUTER_ENDPOINT", "https://api.openrouter.ai/v1")

# Other configuration
DEFAULT_MAX_RESULTS = 5

# Content size thresholds (in characters)
# These control summarization behavior based on content length
TINY_CONTENT_THRESHOLD = int(
    os.getenv("TINY_CONTENT_THRESHOLD", "500")
)  # Skip summarization below this
SMALL_CONTENT_THRESHOLD = int(
    os.getenv("SMALL_CONTENT_THRESHOLD", "2000")
)  # Use extractive/short summary below this
# Content >= 2000 chars uses abstractive/medium (current behavior)

# Backup configuration
ENABLE_AUTO_BACKUP = os.getenv("ENABLE_AUTO_BACKUP", "true").lower() == "true"
BACKUP_INTERVAL_HOURS = int(os.getenv("BACKUP_INTERVAL_HOURS", "24"))
BACKUP_RETENTION_COUNT = int(os.getenv("BACKUP_RETENTION_COUNT", "10"))
BACKUP_PATH = os.getenv("BACKUP_PATH", "./backups")
