## Project Roadmap & Development Plan

Single source for project status, priorities, and planned work. This merges and replaces the previous separate roadmap and development plan.

Last updated: 2025-11-27 (branch: development)

### Status Overview

- Completed

  - Dual-database architecture (SQLite authoritative store + ChromaDB semantic index)
  - MCP tool surface: initialize, store, retrieve, update, delete, list_topics, status, summarize
  - Summary-first retrieval via summary embeddings; regeneration on content change

- In Progress

  - Structured logging and clearer error propagation
  - Test stabilization (migrate from print-based scripts)
  - Documentation refinements (schema, ops, and background docs)

- Next Up
  - Minimal pytest suite (fixtures, temp paths, mock summarizer)
  - Include similarity scores in retrieval responses (optional)

### MVP Focus (Stabilization)

1. Enable SQLite foreign keys per-connection (`PRAGMA foreign_keys=ON`).
2. Fix topic count logic in `_remove_from_topic` (decrement; delete at zero).
3. Standardize response shapes (apply `format_response` consistently; unify empty-result handling).
4. Add minimal tests for the above (topic decrement, FK cascades, summary regeneration).

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

  - Enable FK pragma in `SQLiteConnection`
  - Fix `_remove_from_topic` decrement logic and prune zero-count topics
  - Normalize retrieval response shapes
  - Introduce basic logging via `logging`
  - Add minimal pytest with temp paths and mocked summarizer

- Medium-term (3–4 weeks)
  - Indices for common filters/sorts (e.g., `topic_name`, `created_at`; optional `UNIQUE(memory_id, summary_type)`)
  - Reconciliation script comparing SQLite vs Chroma IDs
  - Pagination for retrieval and topic listing
  - Expand pytest coverage and add simple CI

### Technical Debt & Known Issues

- Error handling/logging: replace prints; propagate structured errors
- Cross-store consistency: no transactional coordination between SQLite and Chroma
- Tests: procedural, print-driven; rely on real paths and network summarization
- Performance: vector search may slow with size; consider indices and caching
- Specific fixes: enforce FKs; correct topic decrement logic

### Documentation Notes

- Clarify FK enforcement requirement in setup and examples
- Document topic count decrement behavior; consider SQL trigger alternative
- Provide a quick mapping between SQLite tables and Chroma collections (IDs/metadata)
- If one summary per type is desired: document `UNIQUE(memory_id, summary_type)`
- Add operational guidance: backup/restore, vacuum, Chroma reset/maintenance

### References

- Database schema and ER diagram: see [docs/database_schema.md](./database_schema.md)
- Background docs: `docs/bg_info_root.md`, `docs/bg_info_db.md`, `docs/bg_info_memory_service.md`, `docs/bg_info_utils.md`, `docs/bg_info_tests.md`
