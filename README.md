# MCP Memory Server

A minimal MCP server that provides persistent, semantic memory for LLM agents using a hybrid store: SQLite (source of truth) + ChromaDB (vector search). Summaries are generated on ingest to enable fast, summary‑first retrieval.

## Overview

- What it is: MCP tools to store, retrieve, update, delete, summarize, list topics, and report status.
- How it works: Write to SQLite + Chroma; summaries stored in both; retrieval searches summary embeddings, then hydrates full text.
- No REST API (MCP only). DB schema and ER diagram are in `docs/database_schema.md`.

## Tech stack

- Python 3.9+
- FastMCP (MCP server)
- SQLite + ChromaDB
- OpenRouter (LLM summaries) via `openai` client wrapper
- dotenv, pydantic

## Install & configure

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

## Run

```bash
python memory_server.py
```

Runs an MCP server over stdio. Point your MCP client to this command (tool namespace: `memory_server`).

## Tools (MCP)

- memory_initialize(reset=False)
- memory_store(content, topic, tags=[])
- memory_retrieve(query, max_results=5, topic=None, return_type="full_text|summary|both")
- memory_update(memory_id, content?, topic?, tags?)
- memory_delete(memory_id)
- memory_list_topics()
- memory_status()
- memory_summarize(memory_id?|query?|topic?, summary_type, length)

## Database

- SQLite tables: topics, memory_items, summaries
- Chroma collections: memory_items, topics, summaries
- Diagram and details: see `docs/database_schema.md`

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

More docs: `background_info.md`, `docs/development_plan.md`.

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
