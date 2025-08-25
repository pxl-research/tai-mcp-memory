## Technical Background (root)

High-level documentation for the MCP Memory Server’s entrypoint, configuration, MCP tool surface, and cross-cutting concerns.

Last updated: 2025-08-25 (branch: development)

### Project overview

An MCP server that provides persistent, semantic memory for LLM agents. It stores full content and metadata in SQLite and semantic embeddings in ChromaDB. The server also generates summaries (via OpenRouter LLM) to enable summary-first retrieval.

### Entrypoint and MCP tools

- Entrypoint: `memory_server.py`

  - Uses `FastMCP` to register prompts and tools, then runs over stdio.
  - On startup, calls `memory_initialize()` (without reset) and prints the result.

- Prompts (discovery helpers):

  - `store_memory_prompt(content, topic?)` – guides clients to call `memory_store` correctly.
  - `recall_memory_prompt(query, topic?)` – guides clients to call `memory_retrieve` and present results succinctly.

- Tools (from `memory_server.py`):
  - `memory_initialize(reset: bool=False) -> dict`
  - `memory_store(content: str, topic: str, tags: List[str]=[]) -> dict`
  - `memory_retrieve(query: str, max_results: int=5, topic?: str, return_type: Literal['full_text','summary','both']='full_text') -> List[dict]`
  - `memory_update(memory_id: str, content?: str, topic?: str, tags?: List[str]) -> dict`
  - `memory_delete(memory_id: str) -> dict`
  - `memory_list_topics() -> List[dict]`
  - `memory_status() -> dict`
  - `memory_summarize(memory_id?: str, query?: str, topic?: str, summary_type: Literal['abstractive','extractive','query_focused']='abstractive', length: Literal['short','medium','detailed']='medium') -> dict`

Note: There is no `memory_delete_empty_topic` tool in the current code; any references in older docs are outdated.

### Configuration (`config.py`)

- Environment variables (loaded via `python-dotenv`):
  - `DB_PATH` (default `./memory_db`) → SQLite file at `${DB_PATH}/memory.sqlite` and Chroma at `${DB_PATH}/chroma`.
  - `OPENROUTER_API_KEY` → Required for summarization.
  - `OPENROUTER_ENDPOINT` (default `https://api.openrouter.ai/v1`) → Not directly used by the client wrapper (which has its own default); keep consistent or wire through.
  - `DEFAULT_MAX_RESULTS` = 5 (used for retrieval defaults).

Repo notes:

- An `.env.example` is provided. Ensure your local `.env` is not committed; rotate any exposed API keys and add `.env` to `.gitignore`.

### Dependencies (`requirements.txt`)

- Declared: `mcp[cli]`, `python-dotenv~=1.1.1`, `chromadb~=1.0.17`, `pydantic`.
- Missing (required by code): `openai` (used by `utils/open_router_client.py` and `utils/summarizer.py`). Add to requirements to avoid runtime import errors.

### Data paths

- Default: `./memory_db/` (SQLite file `memory.sqlite`, Chroma dir `chroma/`). Example `.env` may set `DB_PATH=./data/` – both layouts are supported by config; choose one and keep consistent.

### Cross-cutting concerns and known issues

- Dual writes without transactions: SQLite and Chroma operations are not atomic across stores; partial failures can diverge state.
- SQLite foreign keys: FKs declared with `ON DELETE CASCADE` require `PRAGMA foreign_keys=ON` per connection; not currently enabled in `SQLiteConnection`.
- Topic count bug: `_remove_from_topic` increments instead of decrements; topics may not be cleaned up correctly.
- Retrieval return shape: `retrieve_memory` returns a list of dicts, but returns `[format_response(...)]` in empty/error cases; standardize for clients.
- Tests & external dependency: Tests call live summarization; mock `Summarizer.generate_summary` for CI stability. Tests also write to real paths; prefer temporary directories.
- Security: Do not commit `.env` with secrets. If already committed, rotate API keys immediately and purge history if needed.

### Related documentation

- Component background docs:

  - `db/background_info.md`
  - `memory_service/background_info.md`
  - `utils/background_info.md`
  - `tests/background_info.md`
  - `docs/background_info.md`

- Database schema (with ER Mermaid): `docs/database_schema.md`
- Roadmap and architecture notes: `docs/development_plan.md`
