## Technical Background (memory_service)

This document summarizes the service layer that orchestrates persistence, semantic retrieval, summarization, and status reporting for the MCP Memory Server.

Last updated: 2025-08-25 (branch: development)

### Files overview

- core_memory_service.py

  - Purpose: Core CRUD and retrieval across SQLite (authoritative store) and ChromaDB (semantic index) with automatic summarization via `utils.summarizer.Summarizer` (uses `OPENROUTER_API_KEY`).
  - Dependencies: `SQLiteManager`, `ChromaManager`, `utils.create_memory_id`, `utils.timestamp`, `utils.format_response`, `config.OPENROUTER_API_KEY`.
  - Key functions:
    - `initialize_memory(reset: bool) -> dict`:
      - Calls `sqlite_manager.initialize(reset)` and `chroma_manager.initialize(reset)`; reports combined status.
    - `store_memory(content: str, topic: str, tags: List[str] = []) -> dict`:
      - Generates `memory_id`, stores in SQLite and Chroma, updates Chroma topic doc, generates a medium abstractive summary, stores summary in SQLite and its embedding in Chroma (metadata includes `memory_id`, `summary_type`, `topic`).
      - Returns success with IDs and summary flags; warns but does not fail overall if summary generation/storage fails.
    - `retrieve_memory(query: str, max_results: int = 5, topic: Optional[str] = None, return_type: Literal["full_text","summary","both"] = "full_text") -> List[dict]`:
      - Searches Chroma summary embeddings first for efficiency, then hydrates full records from SQLite. Returns list of results; if none, returns a single `format_response` message element instead of an empty list.
    - `update_memory(memory_id: str, content?: str, topic?: str, tags?: List[str]) -> dict`:
      - Validates existence, updates SQLite, reads back the updated record, updates Chroma memory doc, updates topic (if changed), and regenerates summary if content changed. If a default summary exists (`abstractive_medium`), it updates SQLite and re-stores the embedding in Chroma under the same `summary_id`.
    - `delete_memory(memory_id: str) -> dict`:
      - Deletes memory from SQLite and Chroma; deletes all SQLite summaries for that memory; deletes only the default summary embedding in Chroma if found (others, if any, are not deleted here).
  - Notes and caveats:
    - Summary lifecycle: `store_summary_embedding` uses a Chroma `.add` call; re-storing an existing ID may not update depending on Chroma backend behavior—use an explicit `update` if duplicates are disallowed.
    - Return shape inconsistency: `retrieve_memory` returns a list of dicts on success, but returns `[format_response(...)]` when empty/error; consider standardizing.
    - Cross-store consistency: Failures in one backend don’t trigger rollback in the other.

- auxiliary_memory_service.py
  - Purpose: Auxiliary operations—topic listing, system status aggregation, and ad hoc summarization across selected content.
  - Dependencies: `SQLiteManager`, `ChromaManager`, `utils.summarizer.Summarizer`, `config.DB_PATH`, `OPENROUTER_API_KEY`, `utils.timestamp`, `utils.format_response`.
  - Key functions:
    - `list_topics() -> List[dict]`:
      - Returns topics from SQLite or `[format_response(success=True, message="No topics found")]` when empty.
    - `get_status() -> dict`:
      - Merges SQLite stats and Chroma status with `db_path` and `system_time`.
    - `summarize_memory(memory_id?: str, query?: str, topic?: str, summary_type: Literal["abstractive","extractive","query_focused"] = "abstractive", length: Literal["short","medium","detailed"] = "medium") -> dict`:
      - Accepts one of memory_id/query/topic. If memory_id, summarizes that item. Otherwise, uses Chroma memory search (not summaries) to collect up to 10 items, concatenates content, and summarizes. Uses `query` as guidance only when `summary_type == "query_focused"`.
  - Notes:
    - For query/topic summarization, searching summary embeddings first could be more efficient before hydrating full content.
    - Token usage can grow with concatenation; consider size caps and deduplication.

### Cross-cutting patterns

- Module-level singletons for `SQLiteManager`, `ChromaManager`, and `Summarizer` simplify usage but hinder test isolation and configurability.
- Minimal input validation; callers (MCP tools) likely perform parameter validation.
- `format_response` unifies status responses, but retrieval functions return plain dicts vs wrapped responses; standardization would help clients.

### Risks and limitations

- Concurrency: No explicit locking; SQLite versions records but there’s no optimistic concurrency control surface exposed.
- Consistency: Dual writes (SQLite/Chroma) can diverge on partial failure; no compensation or retry strategy.
- Summaries lifecycle: Updating embeddings by re-adding may fail if IDs must be unique; explicit update/delete may be required.
- Deletion coverage: Only the default summary embedding is deleted from Chroma in `delete_memory`.

### Recommended improvements

1. Introduce a coordinator or repository layer for atomic cross-store operations with retries/compensation.
2. Standardize return shapes for retrieval and empty states; include similarity scores and sources.
3. Add configuration toggles for summary generation and lengths; support async/offline summarization.
4. Prefer summary-embedding search first for both retrieval and summarization workflows; parameterize max results.
5. Add tests covering summary regeneration, cross-store divergence scenarios, and deletion coverage.
