# MCP Server Memory Development Plan (MVP-focused)

## Status Overview

- Completed

  - Core infrastructure with dual-database architecture (SQLite + ChromaDB)
  - Basic MCP API/tool surface: initialize, store, retrieve, update, list_topics, status, delete
  - ChromaDB semantic search wired to summaries
  - SQLite relational storage for authoritative data
  - Single-type summarization with regeneration on content change

- In Progress

  - Error recovery patterns and structured logging
  - Documentation & code comments
  - Test stabilization (move away from print-driven scripts)

- Next Up
  - Minimal pytest suite (fixtures, temp paths, mock summarizer)
  - Optional: include similarity scores in retrieval responses

## MVP Focus (scope and priorities)

Immediate must-do fixes to stabilize current features:

1. Enable SQLite foreign keys: ensure `PRAGMA foreign_keys=ON` per connection.
2. Fix topic count logic: decrement in `_remove_from_topic` and delete topic row at zero.
3. Standardize response shapes: ensure retrieval uses one consistent format (via `format_response`).
4. Add minimal tests for the above (topic decrement, FK cascades, summary regeneration on updates).

## Phases (reframed for MVP)

- Phase 1: Core Infrastructure — MVP Stabilization

  - Structured logging (Python `logging`) to replace prints
  - Basic error handling and propagation across service boundaries
  - MCP tool surface confirmed in server entrypoint
  - Apply MVP must-do fixes (FK pragma, topic decrement, response consistency)

- Phase 2: Memory Management — Pending

  - Defer document chunking; keep single-document summarization for MVP
  - Plan tiered memory and content refresh as post-MVP

- Phase 3: Advanced Features — Pending

  - Summarization: multi-level and quality assessment (deferred)
  - Usage statistics, reasoning layer, access control (deferred)

- Phase 4: Optimization & Scaling — Pending
  - Pagination for retrievals and topic listing
  - Performance tuning and basic caching

## Next Steps

Immediate (1–2 weeks):

- Enable `PRAGMA foreign_keys=ON` in SQLite connections
- Fix `_remove_from_topic` decrement bug and prune zero-count topics
- Normalize retrieval response shapes
- Add minimal pytest suite (temp dirs; mock summarizer)
- Introduce basic logging via `logging`

Medium-term (3–4 weeks):

- Add indices for common filters/sorts (e.g., `topic_name`, `created_at`; optional UNIQUE(memory_id, summary_type))
- Add a reconciliation script to compare IDs across SQLite and Chroma
- Add pagination to retrieval and topic listing
- Expand pytest coverage and add simple CI

## Technical Debt & Known Issues

- Error Handling

  - Lacks structured logging and consistent error propagation
  - No cross-store transaction/compensation logic

- Testing

  - Current tests are print-style scripts
  - Missing targeted tests for FK cascades and topic decrement

- Documentation

  - API usage examples can be expanded
  - MCP client settings now included in README

- Performance

  - Vector search may slow with larger data; plan indexing and pagination
  - Add SQLite indices for common operations

- Specific Bugs/Tasks
  - Enforce SQLite FKs with PRAGMA
  - Fix `_remove_from_topic` decrement logic
