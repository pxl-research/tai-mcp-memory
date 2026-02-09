## Project Roadmap & Development Plan

Single source for project status, priorities, and planned work. This merges and replaces the previous separate roadmap and development plan.

Last updated: 2026-02-06 (branch: development)

### Status Overview

- Completed

  - Dual-database architecture (SQLite authoritative store + ChromaDB semantic index)
  - MCP tool surface: initialize, store, retrieve, update, delete, list_topics, status, summarize
  - Summary-first retrieval via summary embeddings; regeneration on content change
  - **SQLite foreign keys enabled per-connection** (`PRAGMA foreign_keys=ON`) with logging and verification
  - **Topic count decrement logic** working correctly with defensive checks for data integrity
  - **Test suite for FK cascades and topic management** (`tests/test_sqlite_fk_and_topic.py`)
  - **Size-based summarization** (3-tier strategy: tiny/small/large content) with configurable thresholds
  - **Automatic backup system** with thread-safe caching, interval-based backups, and retention management
  - **MCP Resources feature** exposing 4 documentation resources (agents, readme, schema, roadmap) via MCP protocol
  - **Deletion bug fix** for Chroma summary embedding cleanup (retrieve summary ID before memory deletion)

- In Progress

  - Documentation updates for blog post (size-based summarization, MCP resources, backup system)
  - Code quality improvements (logging, type hints, validation) - deferred to post-blog phase

- Next Up
  - Standardize response shapes (apply `format_response` consistently; unify empty-result handling)
  - Minimal pytest suite (fixtures, temp paths, mock summarizer)
  - Include similarity scores in retrieval responses (optional)

### MVP Focus (Stabilization)

1. ~~Enable SQLite foreign keys per-connection (`PRAGMA foreign_keys=ON`).~~ ✅ **COMPLETED**
2. ~~Fix topic count logic in `_remove_from_topic` (decrement; delete at zero).~~ ✅ **COMPLETED**
3. ~~**Fix deletion bug:** Memory deletion leaves Chroma summary embeddings orphaned (retrieve summary ID before deletion).~~ ✅ **COMPLETED**
4. Standardize response shapes (apply `format_response` consistently; unify empty-result handling). **PARTIALLY COMPLETED** (test_return_shape.py validates current behavior)
5. ~~Add minimal tests for FK cascades and topic decrement.~~ ✅ **COMPLETED**
6. ~~Size-based summarization to optimize API costs.~~ ✅ **COMPLETED**
7. ~~Automatic backup system with thread safety.~~ ✅ **COMPLETED**

### Phases

- Phase 1: Core Infrastructure — MVP stabilization

  - Structured logging (`logging`), improved error handling
  - Apply MVP fixes (FK pragma, topic decrement, response consistency)

- Phase 2: Memory Management — Pending

  - Keep single-document summarization for MVP; plan chunking post-MVP
  - Topic lifecycle and maintenance utilities

- Phase 3: Advanced Features — Pending

  - Multi-level summarization, quality assessment, retrieval scoring details
  - Usage statistics, access control (as needed)

- Phase 4: Optimization & Scaling — Pending
  - Pagination for retrievals and topic listing
  - Performance tuning, basic caching

### Next Steps

- Immediate (1–2 weeks)

  - ~~Enable FK pragma in `SQLiteConnection`~~ ✅ **COMPLETED**
  - ~~Fix `_remove_from_topic` decrement logic and prune zero-count topics~~ ✅ **COMPLETED**
  - ~~Introduce basic logging via `logging`~~ ✅ **COMPLETED** (for FK pragma and topic management)
  - ~~**Fix deletion bug:** Retrieve summary ID before deleting memory to prevent orphaned Chroma embeddings~~ ✅ **COMPLETED**
  - ~~Add test for proper Chroma summary embedding deletion~~ ✅ **COMPLETED** (test_deletion_fix.py)
  - Documentation cleanup for blog post (size-based summarization, MCP resources, backups) **IN PROGRESS**
  - Code quality improvements: replace print() with logger, add API key validation, fix type hints **DEFERRED**
  - Normalize retrieval response shapes **DEFERRED** (test_return_shape.py validates current behavior)
  - Add minimal pytest with temp paths and mocked summarizer **DEFERRED**

- Medium-term (3–4 weeks)
  - Indices for common filters/sorts (e.g., `topic_name`, `created_at`; optional `UNIQUE(memory_id, summary_type)`)
  - Reconciliation script comparing SQLite vs Chroma IDs
  - Pagination for retrieval and topic listing
  - Expand pytest coverage and add simple CI

### Technical Debt & Known Issues

- **Code quality:** Print statements in production code (core_memory_service.py, summarizer.py) instead of proper logging
- **Validation:** Missing OPENROUTER_API_KEY validation at startup (fails cryptically during summarization)
- **Type hints:** Invalid type annotations (`any` instead of `Any`, `or None` instead of `Optional[]`)
- **DRY violations:** Timestamp parsing duplicated 3x in backup.py
- **Cross-store consistency:** No transactional coordination between SQLite and Chroma; dual writes can diverge on partial failure
- **Tests:** Some tests still procedural and print-driven; rely on real paths and network summarization (pytest migration in progress)
- **Performance:** Vector search may slow with scale; consider indices and caching
- **Configuration:** Hardcoded headers in OpenRouterClient (HTTP-Referer, X-Title) should be configurable

### Documentation Notes

- ~~Clarify FK enforcement requirement in setup and examples~~ ✅ **COMPLETED** (FK pragma now enabled and documented)
- ~~Document topic count decrement behavior~~ ✅ **COMPLETED** (topic management verified and tested)
- Provide a quick mapping between SQLite tables and Chroma collections (IDs/metadata)
- If one summary per type is desired: document `UNIQUE(memory_id, summary_type)`
- Add operational guidance: backup/restore, vacuum, Chroma reset/maintenance

### References

- Database schema and ER diagram: see [docs/database_schema.md](./database_schema.md)
- Background docs: `docs/bg_info_root.md`, `docs/bg_info_db.md`, `docs/bg_info_memory_service.md`, `docs/bg_info_utils.md`, `docs/bg_info_tests.md`
