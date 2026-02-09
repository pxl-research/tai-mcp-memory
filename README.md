# MCP Memory Server

## Project Overview

The MCP Memory Server provides persistent, semantic memory for LLM agents. It combines SQLite for structured storage and ChromaDB for vector-based semantic search, with automatic summarization for efficient retrieval.

**Technologies**: Python 3.10+, FastMCP, SQLite, ChromaDB, OpenRouter (LLM summarization)

## Available Tools

- `memory_store` - Store new memories with topic and tags
- `memory_retrieve` - Semantic search across memories
- `memory_update` - Update existing memories
- `memory_list_topics` - List all topics with memory counts
- `memory_status` - Check database statistics
- `memory_summarize` - Manually trigger summarization

## Quick Start

```bash
# 1. Install uv
pip install uv

# 2. Clone and setup
git clone <repository-url>
cd tai-mcp-memory
uv sync --no-install-project

# 3. Configure environment
cp .env.example .env  # Or create .env manually
# Add your OPENROUTER_API_KEY to .env

# 4. Add to Claude Code
claude mcp add --transport stdio tai-memory -- \
  uv --directory $(pwd) run memory_server.py

# 5. Verify
claude mcp list
```

## Configuration

Create a `.env` file in the project root:

```bash
# Required
OPENROUTER_API_KEY=sk-or-v1-your-key-here

# Optional
DB_PATH=./memory_db                              # Default: ./memory_db
OPENROUTER_ENDPOINT=https://api.openrouter.ai/v1 # Default: https://api.openrouter.ai/v1

# Backup configuration (optional)
ENABLE_AUTO_BACKUP=true                          # Default: true
BACKUP_INTERVAL_HOURS=24                         # Default: 24
BACKUP_RETENTION_COUNT=10                        # Default: 10
BACKUP_PATH=./backups                            # Default: ./backups
```

**Note**: Without a valid `OPENROUTER_API_KEY`, storage works but automatic summarization will be disabled.

## Automatic Backups

The memory server includes automatic backup functionality to protect your data.

### How It Works

- **Automatic backups** are created every 24 hours (configurable) when storing new memories
- Backups are **completely transparent** - no action required from users or LLM agents
- The system keeps the **last 10 backups** by default and automatically removes older ones
- Backups are stored as timestamped zip files in the `./backups` directory

### Configuration

Control backup behavior via environment variables in `.env`:

```bash
ENABLE_AUTO_BACKUP=true           # Enable/disable automatic backups
BACKUP_INTERVAL_HOURS=24          # Hours between automatic backups
BACKUP_RETENTION_COUNT=10         # Number of backups to keep
BACKUP_PATH=./backups             # Where to store backups
```

### Restoring from Backup

To restore from a backup, use the standalone restore script:

```bash
# Interactive mode - select from available backups
python restore_memory.py

# Or specify a backup file directly
python restore_memory.py --file backups/memory_backup_2026-01-29_14-30-00.zip
```

**Safety features:**
- Lists all available backups with timestamps and sizes
- Creates a safety backup of your current database before restoring
- Requires explicit confirmation before proceeding
- Clear error messages if something goes wrong

**Note:** After restoring, you may need to restart the MCP server for changes to take effect.

### Disabling Automatic Backups

If you have your own backup strategy, you can disable automatic backups:

```bash
# In .env
ENABLE_AUTO_BACKUP=false
```

## Size-Based Summarization

The system automatically chooses the summarization strategy based on content size to optimize API costs and relevance:

- **Tiny (<500 chars)**: No LLM call, uses content directly (cost-efficient)
  - Common for preferences, short notes
  - Example: "User prefers snake_case for variable names"

- **Small (500-2000 chars)**: Extractive summary (fast, concise)
  - LLM extracts key sentences from the content
  - Common for meeting notes, code explanations

- **Large (≥2000 chars)**: Abstractive summary (comprehensive)
  - LLM generates 3-5 sentence summary
  - Common for documentation, articles

Configure thresholds in `.env` (optional):
```bash
TINY_CONTENT_THRESHOLD=500    # Default: skip LLM for content under 500 chars
SMALL_CONTENT_THRESHOLD=2000  # Default: use extractive summary under 2000 chars
```

**Why this matters**: Small snippets don't benefit from abstractive summarization and waste API tokens. This approach saves costs while maintaining semantic search quality.

## MCP Client Integration

### Claude Code (Recommended)

```bash
claude mcp add --transport stdio tai-memory -- \
  uv --directory /path/to/tai-mcp-memory run memory_server.py
```

Replace `/path/to/tai-mcp-memory` with your actual project path.

Verify connection:
```bash
claude mcp list
```

### Other MCP Clients (VS Code/Cline, etc.)

Add to your MCP client configuration:

```json
{
  "memory_server": {
    "type": "stdio",
    "command": "uv",
    "args": [
      "--directory",
      "/path/to/tai-mcp-memory/",
      "run",
      "memory_server.py"
    ]
  }
}
```

### Accessing Documentation via MCP

The server exposes documentation as queryable resources that LLM agents can retrieve programmatically:

- `memory://docs/agents` - Usage guidelines for LLM agents
- `memory://docs/readme` - This README file
- `memory://docs/schema` - Database schema documentation
- `memory://docs/roadmap` - Project status and roadmap

LLM agents can retrieve these via MCP protocol without requiring file system access. This enables agents to self-discover best practices and stay updated on available features.

## Usage Patterns

The memory system is designed for **proactive use** by LLM agents. Here are common patterns:

### Pattern 1: Starting Every Conversation

Always check for relevant context at the beginning of a conversation:

```
Assistant: Let me check if I have any context about your project...
[calls memory_retrieve(query="user preferences project context", max_results=5)]

# If memories found:
Assistant: I see we've been working on the authentication system. I remember
you prefer JWT tokens with refresh tokens stored in httpOnly cookies...
```

### Pattern 2: User Shares Preferences

Store preferences immediately when user provides them:

```
User: I prefer functional programming and try to avoid classes when possible.

[calls memory_store(
  content="User prefers functional programming style and avoids classes when possible",
  topic="user_preferences",
  tags=["coding_style", "functional"]
)]
```

### Pattern 3: User References Past Work

Retrieve context when user mentions previous interactions:

```
User: Remember when we implemented that authentication system?

[calls memory_retrieve(query="authentication system implementation", topic="project_architecture", max_results=5)]
```

### Pattern 4: Completing Significant Work

Store architectural decisions and rationale after completing work:

```
# After implementing JWT authentication with refresh tokens
[calls memory_store(
  content="Implemented JWT authentication system using access tokens (15min expiry) and refresh tokens (7 days) stored in httpOnly cookies. Chose this approach for security and to prevent XSS attacks on tokens.",
  topic="project_architecture",
  tags=["authentication", "security", "jwt"]
)]
```

### Pattern 5: Checking for Existing Patterns

Before making recommendations, check for past decisions:

```
User: Should we use Redux for state management?

[calls memory_retrieve(query="state management decisions patterns", max_results=3)]

# If past decisions found about preferring simpler solutions:
Assistant: Based on our previous discussions, you've preferred simpler solutions.
Given your project size, React Context might be more appropriate than Redux...
```

## Development

### Alternative Installation (pip)

If you prefer traditional Python environments:

```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Running Tests

The project includes 11 test files covering core functionality, database operations, backups, and bug fixes:

```bash
# Using uv (recommended)
uv run tests/test_sqlite_manager.py
uv run tests/test_chroma_manager.py
uv run tests/test_core_memory_service.py
uv run tests/test_auxiliary_memory_service.py
uv run tests/test_backup.py
uv run tests/test_backup_race_condition.py
uv run tests/test_deletion_fix.py
uv run tests/test_return_shape.py
uv run tests/test_openrouter_config.py
uv run tests/test_sqlite_fk_and_topic.py
uv run tests/test_update_topic_cascade_bug.py

# Using Python (with activated venv)
python tests/test_sqlite_manager.py
python tests/test_chroma_manager.py
# ... (same pattern for all 11 test files)
```

**Note:** Some tests require `OPENROUTER_API_KEY` in `.env` for LLM summarization calls.

### Database Structure

- **SQLite tables**: topics, memory_items, summaries
- **Chroma collections**: memory_items, topics, summaries
- See [database_schema.md](docs/database_schema.md) for details

**Note**: Dual writes are not atomic across SQLite/Chroma.

### Background Documentation

- [Root folder background](docs/bg_info_root.md)
- [Database layer (`db/`)](docs/bg_info_db.md)
- [Memory service layer (`memory_service/`)](docs/bg_info_memory_service.md)
- [Utilities (`utils/`)](docs/bg_info_utils.md)
- [Tests (`tests/`)](docs/bg_info_tests.md)

## License

This project is licensed under the [PolyForm Noncommercial License 1.0.0](LICENSE).

**Free for:**
- Personal use, research, and experimentation
- Educational institutions and students
- Charitable and non-profit organizations
- Government institutions
- Hobby projects and amateur pursuits

**Not permitted:**
- Commercial use without permission

For commercial licensing inquiries, please open an issue on GitHub.
