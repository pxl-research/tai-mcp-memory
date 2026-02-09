## Project Roadmap & Development Plan

Single source for project status, priorities, and planned work. This merges and replaces the previous separate roadmap and development plan.

Last updated: 2026-02-09 (branch: development)

### Current Focus

The core memory system is **stable and feature-complete** for the initial release. Current priorities:

1. **Response consistency** - Standardize response shapes across all MCP tools
2. **Testing improvements** - Migrate to pytest with fixtures and mocked dependencies
3. **Documentation** - Operational guides for backup/restore, vacuum, Chroma maintenance

### Development Phases

- Phase 2: Memory Management
  - Topic lifecycle and maintenance utilities
  - Chunking strategy for large documents (post-MVP)

- Phase 3: Advanced Features
  - Multi-level summarization
  - Quality assessment and retrieval scoring details
  - Usage statistics, access control (as needed)

- Phase 4: Optimization & Scaling
  - Pagination for retrievals and topic listing
  - Performance tuning and caching strategies
  - Database indices for common filters/sorts

### Next Steps

**Immediate** (1-2 weeks):
- Normalize retrieval response shapes (test_return_shape.py validates current behavior)
- Add minimal pytest with temp paths and mocked summarizer
- Operational documentation: backup/restore, vacuum, Chroma reset/maintenance

**Medium-term** (3-4 weeks):
- Indices for common filters/sorts (e.g., `topic_name`, `created_at`)
- Reconciliation script comparing SQLite vs Chroma IDs
- Pagination for retrieval and topic listing
- Expand pytest coverage and add simple CI

### Known Issues & Technical Debt

- **Cross-store consistency:** No transactional coordination between SQLite and Chroma; dual writes can diverge on partial failure
- **Tests:** Some tests still procedural and print-driven; rely on real paths and network summarization (pytest migration in progress)
- **Performance:** Vector search may slow with scale; consider indices and caching
- **Configuration:** Hardcoded headers in OpenRouterClient (HTTP-Referer, X-Title) should be configurable

### Documentation Backlog

- Provide mapping between SQLite tables and Chroma collections (IDs/metadata alignment)
- Document `UNIQUE(memory_id, summary_type)` constraint option
- Add operational guidance: backup/restore, vacuum, Chroma reset/maintenance

### References

- Database schema and ER diagram: see [docs/database_schema.md](./database_schema.md)
- Background docs: `docs/bg_info_root.md`, `docs/bg_info_db.md`, `docs/bg_info_memory_service.md`, `docs/bg_info_utils.md`, `docs/bg_info_tests.md`
