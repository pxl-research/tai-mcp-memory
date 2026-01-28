# MCP Memory Server

## Project Overview

The MCP Memory Server provides persistent, semantic memory for LLM agents. It combines SQLite for structured storage and ChromaDB for vector-based semantic search, with automatic summarization for efficient retrieval.

## Technologies Used

- Python 3.9+
- FastMCP
- SQLite
- ChromaDB
- OpenRouter (LLM summarization)
- python-dotenv, pydantic, openai

## Installation Instructions

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Create `.env` (or export):

```
DB_PATH=./memory_db
OPENROUTER_API_KEY=sk-or-v1-...
OPENROUTER_ENDPOINT=https://api.openrouter.ai/v1  # optional
```

## Running the Project

```bash
python memory_server.py
```

Runs an MCP server over stdio. Point your MCP client to this command (tool namespace: `memory_server`).

## Usage Patterns

The memory system is designed for **proactive use** by LLM agents. Here are common patterns and examples:

### Pattern 1: Starting Every Conversation

**Always check for relevant context at the beginning of a conversation:**

```
Assistant: Let me check if I have any context about your project...
[calls memory_retrieve(query="user preferences project context", max_results=5)]

# If memories found:
Assistant: I see we've been working on the authentication system. I remember
you prefer JWT tokens with refresh tokens stored in httpOnly cookies...
```

### Pattern 2: User Shares Preferences

**Store preferences immediately when user provides them:**

```
User: I prefer functional programming and try to avoid classes when possible.

[calls memory_store(
  content="User prefers functional programming style and avoids classes when possible",
  topic="user_preferences",
  tags=["coding_style", "functional"]
)]
```

### Pattern 3: User References Past Work

**Retrieve context when user mentions previous interactions:**

```
User: Remember when we implemented that authentication system?

[calls memory_retrieve(query="authentication system implementation", topic="project_architecture", max_results=5)]
```

### Pattern 4: Completing Significant Work

**Store architectural decisions and rationale after completing work:**

```
# After implementing JWT authentication with refresh tokens
[calls memory_store(
  content="Implemented JWT authentication system using access tokens (15min expiry) and refresh tokens (7 days) stored in httpOnly cookies. Chose this approach for security and to prevent XSS attacks on tokens.",
  topic="project_architecture",
  tags=["authentication", "security", "jwt"]
)]
```

### Pattern 5: Checking for Existing Patterns

**Before making recommendations, check for past decisions:**

```
User: Should we use Redux for state management?

[calls memory_retrieve(query="state management decisions patterns", max_results=3)]

# If past decisions found about preferring simpler solutions:
Assistant: Based on our previous discussions, you've preferred simpler solutions.
Given your project size, React Context might be more appropriate than Redux...
```

## Database

- SQLite tables: topics, memory_items, summaries
- Chroma collections: memory_items, topics, summaries
- Diagram and details: see [database_schema.md](docs/database_schema.md)

## Testing

```bash
python tests/test_sqlite_manager.py
python tests/test_chroma_manager.py
python tests/test_core_memory_service.py
python tests/test_auxiliary_memory_service.py
```

## Notes

- Dual writes are not atomic across SQLite/Chroma.
- Enable a valid OPENROUTER_API_KEY for summarization; without it, storage works but summaries won't.
- Tags are stored comma‑separated in SQLite.

## Background Information

- [Root folder background](docs/bg_info_root.md)
- [Database layer (`db/`)](docs/bg_info_db.md)
- [Memory service layer (`memory_service/`)](docs/bg_info_memory_service.md)
- [Utilities (`utils/`)](docs/bg_info_utils.md)
- [Tests (`tests/`)](docs/bg_info_tests.md)

## MCP client integration (example)

Add this server to your MCP client settings (VS Code/Cline, Claude Code, etc.) to run over stdio. Adjust paths for your environment.

```json
{
  "memory_server": {
    "autoApprove": [
      "memory_store",
      "memory_retrieve",
      "memory_update",
      "memory_list_topics",
      "memory_status",
      "memory_summarize"
    ],
    "disabled": false,
    "timeout": 60,
    "type": "stdio",
    "command": "uv",
    "args": [
      "--directory",
      "/path/to/tai-mcp-memory/",
      "run",
      "memory_server.py"
    ],
    "env": {
      "DB_PATH": "/path/to/tai-mcp-memory/data/"
    }
  }
}
```

Notes:

- Replace `/path/to/tai-mcp-memory/` with your local path.
- You can also run with `python memory_server.py` if you’re not using `uv`.

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
