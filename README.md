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
- Enable a valid OPENROUTER_API_KEY for summarization; without it, storage works but summaries won’t.
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
