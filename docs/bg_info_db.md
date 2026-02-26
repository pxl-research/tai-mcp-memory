## Technical Background (db)

This document summarizes the database layer components for the MCP Memory Server.

Last updated: 2026-01-28 (branch: development)

### Files overview

- **init**.py

  - Exposes `SQLiteManager` and `ChromaManager` via `__all__` with a brief module docstring. No runtime logic.

- chroma_manager.py

  - Purpose: Manage a persistent `chromadb.PersistentClient` and collections for semantic search across memories, topics, and summary embeddings.
  - Collections (from `config`): `MEMORY_COLLECTION`, `TOPICS_COLLECTION`, `SUMMARY_COLLECTION`.
  - Key operations:
    - `initialize(reset=False)`: Optionally resets the Chroma store and ensures all collections exist.
    - `store_memory(memory_id, content, topic, tags)`: Adds a document and metadata; `tags` serialized as JSON; timestamps via `utils.helpers.timestamp()`.
    - `search_memories(query, max_results=5, topic=None)`: Semantic search with optional `where={"topic": topic}` filter; returns list of matching IDs.
    - `update_memory(memory_id, content?, topic?, tags?)`: Reads existing metadata and document, merges updates, and writes back.
    - `delete_memory(memory_id)`: Deletes by ID.
    - `get_status()`: Returns `chroma_collection_count` and `chroma_path`.
    - Summary embeddings: `store_summary_embedding`, `search_summary_embeddings`, `get_summary_by_id`, `delete_summary_embeddings` on `SUMMARY_COLLECTION`.
    - Topics: `update_topic(topic, tags?)` upserts topic metadata (tags JSON or None) and a synthesized description; `get_topic(topic)` fetches metadata.
  - Notes: Exceptions print errors and tracebacks (diagnostic but unstructured); `Settings(allow_reset=True)` is used.

- sqlite_connection.py

  - Purpose: Thin context manager around `sqlite3.connect(db_path)` with `row_factory = sqlite3.Row` for dict-like access.
  - **Foreign key enforcement**: Now enables `PRAGMA foreign_keys = ON` per connection with error logging. Falls back gracefully for older SQLite versions.
  - Considerations: WAL mode (`PRAGMA journal_mode = WAL`) could be enabled for better multi-reader support if needed.

- sqlite_manager.py
  - Purpose: Structured persistence in SQLite for topics, memories, and summaries; complements the vector store.
  - Schema creation in `initialize(reset=False)` using names from `config`:
    - Topics (`TOPICS_COLLECTION`):
      - `name TEXT PRIMARY KEY`, `description TEXT`, `item_count INTEGER DEFAULT 0`, `created_at TEXT NOT NULL`, `updated_at TEXT NOT NULL`.
    - Memory (`MEMORY_COLLECTION`):
      - `id TEXT PRIMARY KEY`, `content TEXT NOT NULL`, `topic_name TEXT NOT NULL`, `tags TEXT`, `created_at TEXT NOT NULL`, `updated_at TEXT NOT NULL`, `version INTEGER DEFAULT 1`,
        FK `(topic_name)` → topics(`name`) ON DELETE CASCADE.
    - Summaries (`SUMMARY_COLLECTION`):
      - `id TEXT PRIMARY KEY`, `memory_id TEXT NOT NULL`, `summary_type TEXT NOT NULL`, `summary_text TEXT NOT NULL`, `created_at TEXT NOT NULL`, `updated_at TEXT NOT NULL`,
        FK `(memory_id)` → memory(`id`) ON DELETE CASCADE.
  - CRUD operations:
    - `store_memory(...)`: Ensures topic exists via `_add_to_topic` then inserts memory; tags stored as comma-separated string.
    - `get_memory(memory_id)`: Returns a dict including parsed `tags` list and `version`.
    - `update_memory(...)`: Updates fields, increments `version`, and if topic changes, decrements old and increments new topic counts.
    - `delete_memory(memory_id)`: Deletes memory and updates the topic count.
    - `list_topics()`: Returns topics ordered by `updated_at`.
    - `get_status()`: Aggregates counts, top topics, and latest item timestamp.
    - Summaries: `store_summary`, `list_summary_types_by_memory_id`, `get_summary`, `get_summary_by_id`, `update_summary`.
      - Note: `delete_summaries` was removed as CASCADE handles deletion automatically when memory is deleted.
  - Internal helpers:
    - `_add_to_topic(topic, conn)`: Creates topic with `item_count=1` if missing; else increments the count and updates `updated_at`.
    - `_remove_from_topic(topic, conn)`: **Fixed** — Now correctly decrements `item_count` and deletes the topic when count reaches 1 (last item removed). Includes improved error logging.
    - `_query_fetch(query, all=True)`: Generic fetch helper; currently unused elsewhere (candidate for removal).

### Schema and relationships (as implemented)

- topics(`name` PK) 1—\* memory(`topic_name` FK)
- memory(`id` PK) 1—\* summaries(`memory_id` FK)

### Considerations and risks

- ~~SQLite foreign keys: Declared FKs require `PRAGMA foreign_keys = ON;` per connection.~~ ✅ **RESOLVED** — FK pragma now enabled in `SQLiteConnection` with logging and verification.
- Concurrency & durability: Consider enabling `PRAGMA journal_mode = WAL;` and `PRAGMA synchronous = NORMAL` for better multi-reader support.
- Tags modeling: Comma-separated storage can break with commas and hinders querying; consider a junction table or JSON.
- Cross-store consistency: SQLite and Chroma writes occur independently; partial failures can cause divergence without a unit-of-work.

### Recommended improvements (non-breaking)

1. ~~Fix `_remove_from_topic` decrement logic with a floor at 0 and delete-row behavior when count reaches 0.~~ ✅ **COMPLETED**
2. ~~Enable `PRAGMA foreign_keys = ON` in `SQLiteConnection.__enter__`~~ ✅ **COMPLETED**; optionally enable WAL (future).
3. Add indices: `{MEMORY_COLLECTION}(topic_name)` ✅ **DONE**, `{MEMORY_COLLECTION}(created_at)` ✅ **DONE**, `{SUMMARY_COLLECTION}(memory_id, summary_type)` ✅ **DONE**.
4. Replace `print` with `logging` and return structured errors; consider propagating exceptions for upstream handling. **Partially done** (FK pragma and topic management have logging; other modules still need updates).
5. ~~Add tests for topic count transitions and FK cascades.~~ ✅ **COMPLETED** (`tests/test_sqlite_fk_and_topic.py`). Still need: basic Chroma operations tests.
