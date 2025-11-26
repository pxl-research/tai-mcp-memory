## Technical Background (docs)

Documentation assets describing schema, architecture, and development roadmap.

Last updated: 2025-08-25 (branch: development)

### Files overview

- database_schema.md

  - Contents: SQLite-focused ER diagram (Mermaid), detailed table specs for `topics`, `memory_items`, and `summaries`; conceptual Chroma collections mapping; data flow summary; integrity/risk notes; suggested enhancements and reference SQL.
  - Key takeaways (as reflected in current code):
    - Tables and relationships match `db/sqlite_manager.py` create statements.
    - Foreign keys require `PRAGMA foreign_keys=ON` which is not enabled in `db/sqlite_connection.py`.
    - `item_count` maintenance depends on correct increment/decrement; current implementation has a decrement bug in `_remove_from_topic` (increments instead of decrements).
    - Tags stored comma-separated; consider JSON or a junction table for robustness and queryability.

- development_plan.md
  - Contents: Project status board, phased roadmap, high-level architecture (SQLite + Chroma), data flow diagrams, MCP tool implementation outline (with code snippets), lessons learned, and next steps.
  - Alignment notes (vs current repository):
    - "Cross-database synchronization mechanism" is marked complete, but the code performs separate writes to SQLite and Chroma without a transactional coordinator; treat as aspirational or pending refinement.
    - MCP server/tool examples are illustrative; the actual MCP server entry (`memory_server.py`) defines the concrete tool interface for this repo (to be validated in the root background doc step).
    - Architecture diagram reference `architecture_diagram.png` may be a placeholder if the image isn’t present in the repo.

### Suggested doc updates

1. Clarify that SQLite foreign key enforcement must be enabled per-connection; reflect this in setup instructions and examples.
2. Note the current `_remove_from_topic` bug and the intended fix; optionally include a SQL trigger alternative.
3. Add an explicit mapping table between SQLite tables and Chroma collections (IDs, metadata fields) for quick reference.
4. If one summary per type per memory is desired, document the `UNIQUE(memory_id, summary_type)` constraint and include the SQL.
5. Consider adding an operational guide: backup/restore, vacuum, Chroma reset, and maintenance tasks.

### Links to generated artifacts

- Database schema and ER diagram: see `docs/database_schema.md` (Mermaid ER section).
