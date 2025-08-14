# MCP Server for Persistent Memory

An extensible Model Context Protocol (MCP) server that provides persistent, queryable, summarizable memory for Large Language Models (LLMs). It enables an AI agent (client) to offload long‑term context into a hybrid storage layer and retrieve the most relevant knowledge on demand via semantic search and summaries.

## 🚀 Why This Exists

LLMs have finite context windows. This server acts as an external episodic + semantic memory so the model can:

- Persist important facts across sessions.
- Retrieve context by meaning (vector semantic search) not just keywords.
- Organize information by topic and tags.
- Maintain evolving knowledge (updates + versioning).
- Generate on‑demand and automatic summaries to compress content.

## 🧱 Architecture Overview

Hybrid dual-database design:

- **SQLite** (relational source of truth): Full text, metadata (topics, tags, timestamps, versions), summaries.
- **ChromaDB** (vector index): Semantic embeddings for full content & summaries (summary-first retrieval for efficiency).

Flow (Store → Retrieve):

1. Client calls `memory_store` with content.
2. Item stored in SQLite (authoritative) + vectorized into Chroma.
3. Abstractive medium summary generated and stored (SQLite + Chroma) for fast future retrieval.
4. `memory_retrieve` queries summary embeddings first, then hydrates full text.

Resilience note: Writes are not currently transactional across both backends—future enhancement listed below.

## 📁 Directory Structure (key parts)

```
memory_server.py        # MCP tool registration & server entrypoint
config.py               # Environment-driven configuration
db/                     # Persistence layer (SQLite + Chroma managers)
memory_service/         # Core + auxiliary service operations (CRUD, summarize, status)
utils/                  # Helpers, summarizer + OpenRouter client wrapper
tests/                  # Script-style validation tests (print PASS/FAIL)
background_info.md      # High-level technical architecture overview
docs/database_schema.md # Database schema (SQLite + Chroma conceptual mapping)
development_plan.md     # Roadmap & phased plan
```

Linked references:

- Server entrypoint: [`memory_server.py`](./memory_server.py)
- Configuration: [`config.py`](./config.py)
- Persistence layer: [`db/`](./db)
- Services: [`memory_service/`](./memory_service)
- Utilities: [`utils/`](./utils)
- Tests: [`tests/`](./tests)
- High-level technical doc: [`background_info.md`](./background_info.md)
- Database schema: [`docs/database_schema.md`](./docs/database_schema.md)
- Development plan / roadmap: [`development_plan.md`](./development_plan.md)

## 🛠 Technology Stack

- Language: Python 3.9+
- Protocol: `FastMCP` (Model Context Protocol server implementation)
- Vector Store: `ChromaDB`
- Relational Store: `SQLite` (file-based)
- Summarization: OpenRouter-accessed LLM (default model `openai/gpt-4o-mini` via custom wrapper)
- Config: `python-dotenv`
- Validation / Metadata: `pydantic` (for tool parameter schemas)
- (Planned potential additions: logging, retries, metrics)

## ✅ Features

- Memory CRUD with topic + tag metadata
- Hybrid semantic retrieval (summary-first for efficiency)
- Automatic summary generation on ingest
- On-demand summarization (abstractive, extractive, query-focused; short/medium/detailed)
- Topic statistics and system status reporting
- Versioning of memory records (increment on update)

## ⚙️ Installation

### Prerequisites

- Python 3.9+
- `pip` (or `uv`) and an OpenRouter API key for summarization

### Clone & Install

```bash
git clone <your-fork-or-clone-url>
cd tai-mcp-memory
python -m venv .venv && source .venv/bin/activate  # optional but recommended
pip install -r requirements.txt
# or
uv pip install -r requirements.txt
```

### Environment Configuration

Create a `.env` file (or export variables):

```
DB_PATH=./memory_db                # (optional) root directory for SQLite & Chroma data
OPENROUTER_API_KEY=sk-or-v1-xxxx   # required for summarization
OPENROUTER_ENDPOINT=https://api.openrouter.ai/v1  # optional override
```

Defaults:

- If `DB_PATH` omitted → `./memory_db`
- If `OPENROUTER_API_KEY` missing → summarization & summary-based retrieval will degrade (warnings printed)

## ▶️ Running the Server

```bash
python memory_server.py
```

This:

1. Initializes (or optionally resets when tool invoked) both databases.
2. Exposes MCP tools over stdio (for integration with an MCP-compatible client/runtime).

To integrate, point your MCP-capable client to run `python memory_server.py` and register the tool namespace `memory_server`.

## 🧪 Testing

Current tests are procedural scripts (print PASS/FAIL). To exercise them:

```bash
python tests/test_sqlite_manager.py      # see file: ./tests/test_sqlite_manager.py
python tests/test_chroma_manager.py      # see file: ./tests/test_chroma_manager.py
python tests/test_core_memory_service.py # see file: ./tests/test_core_memory_service.py
python tests/test_auxiliary_memory_service.py # see file: ./tests/test_auxiliary_memory_service.py
```

Planned improvement: migrate to `pytest` with fixtures & assertions.

## 🔧 MCP Tools (API Surface)

Core & auxiliary operations exposed via MCP (argument types enforced by pydantic):

- `memory_initialize(reset: bool=False)` – (Re)create or reset both stores.
- `memory_store(content: str, topic: str, tags: List[str]=[])` – Persist new memory + auto-summary.
- `memory_retrieve(query: str, max_results: int=5, topic?: str, return_type: full_text|summary|both)` – Semantic retrieval.
- `memory_update(memory_id: str, content?: str, topic?: str, tags?: List[str])` – Update + regenerate summary if content changed.
- `memory_delete(memory_id: str)` – Remove memory + associated summaries.
- `memory_list_topics()` – Topic metadata with counts.
- `memory_status()` – Aggregate system stats.
- `memory_summarize(memory_id?|query?|topic?, summary_type=abstractive|extractive|query_focused, length=short|medium|detailed)` – Ad hoc summarization.

Example JSON-style invocation payload (conceptual):

```json
{
  "tool": "memory_store",
  "args": {
    "content": "Postgres uses MVCC for concurrency.",
    "topic": "databases",
    "tags": ["postgres", "concurrency"]
  }
}
```

## 🧬 Data Model (SQLite)

Tables:

- `topics(name, description, item_count, created_at, updated_at)`
- `memory_items(id, content, topic_name, tags, created_at, updated_at, version)`
- `summaries(id, memory_id, summary_type, summary_text, created_at, updated_at)`

Vector Collections (Chroma):

- `memory_items` – embeddings of full content
- `topics` – topic embeddings (simple descriptive text)
- `summaries` – embeddings of generated summaries (primary retrieval surface)

## 🔄 Retrieval Strategy

1. Query hits summary embeddings first for speed & compression.
2. For each summary match, hydrate full record from SQLite.
3. Optionally return full text, summary, or both.

## ⚠️ Known Limitations / Future Enhancements

- No atomic transaction across SQLite + Chroma (risk of partial writes).
- `_remove_from_topic` logic bug (increments instead of decrement) – needs fix.
- Tags stored as comma-separated string (comma in tag breaks parsing).
- No auth / access control.
- No structured logging; uses `print`.
- Tests depend on live summarization API (should mock).
- No pagination or score metadata in retrieval response.

Planned / Suggested:

- Introduce repository layer with compensating write rollback.
- Switch tags to normalized table or JSON.
- Add logging + metrics + health endpoint.
- Add configurable embedding model & summarization strategy (async / batch).
- Implement reconciliation job (compare IDs across stores).

## 🧩 Extending

- New summary type: Add generation branch in `Summarizer` and adapt store/retrieve logic for additional summary embeddings.
- Alternative vector store: Implement a manager matching `ChromaManager` interface.
- Authorization: Wrap MCP tool functions with access checks.

## 🛡 Operational Notes

- Disk Footprint: Grows with both raw content + embeddings; consider retention or archiving policies.
- Backups: Copy `DB_PATH` directory (contains both SQLite file + Chroma directory).
- Failure Mode: If summarization API key missing, memory still stores; summary-dependent retrieval less effective.

## 📚 Additional Technical Docs

See root [`background_info.md`](./background_info.md) and the database schema document [`docs/database_schema.md`](./docs/database_schema.md) for deeper implementation notes. The phased roadmap lives in [`docs/development_plan.md`](./docs/development_plan.md).

## ❓ FAQ

Q: Can I disable automatic summaries?  
A: Not yet—would require a flag around `store_memory` summarization calls.

Q: Do retrieval results include similarity scores?  
A: Currently no; extend `retrieve_memory` to include them from Chroma query output.

Q: How do I reset everything?  
A: Call `memory_initialize(reset=True)` (deletes & recreates collections / tables).

## 📄 License

No license file detected. Add a LICENSE (e.g., MIT, Apache-2.0) to clarify usage rights.

---

Maintained by the PXL Smart ICT team.  
Contributions & issues welcome.
