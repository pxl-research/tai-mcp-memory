## Technical Background (tests)

The tests are procedural scripts (print-based PASS/FAIL) that exercise core flows across SQLite, Chroma, and service orchestration. Naming would allow pytest discovery, but they currently rely on prints rather than assertions. The project now has 11 test files covering the full system.

Last updated: 2026-02-06 (branch: development)

### Files overview (11 total)

**Original Core Tests:**

- test_chroma_manager.py

  - Covers: init, store/update/delete memory; topic update/get; status; summary embedding CRUD and search.
  - Style: Direct calls with prints; uses `CHROMA_PATH` and resets directory via `shutil.rmtree` before tests.

- test_sqlite_manager.py

  - Covers: DB init/reset, memory CRUD, topic listing, status, summaries CRUD, and delete operations; prints results and some returned structures.

- test_sqlite_fk_and_topic.py

  - Dedicated test for topic count management and foreign key behavior.
  - Tests topic count increments on memory creation and decrements on deletion.

- test_core_memory_service.py

  - Covers: initialize, store, retrieve (return_type="both"), update (content then topic/tags), delete; prints status and payloads.
  - Gap: No explicit checks for Chroma summary embedding cleanup after delete. **Important:** Due to a bug in `delete_memory`, Chroma summary embeddings may be orphaned (see bg_info_memory_service.md).

- test_auxiliary_memory_service.py
  - Covers: list_topics (empty vs populated), get_status (empty vs with data), summarize_memory by memory_id/query/topic.
  - External dependency: Requires valid `OPENROUTER_API_KEY`; otherwise summarization calls may fail and cause flakiness.

**New Tests (Added Post-MVP):**

- test_backup.py
  - Covers: Automatic backup creation, retention policy enforcement, timestamp parsing, cleanup of old backups.
  - Tests `should_create_backup()`, `create_backup()`, `cleanup_old_backups()`, `list_backups()` from `utils.backup`.
  - Validates backup interval logic and retention count limits.

- test_backup_race_condition.py
  - Covers: Thread-safe backup caching with concurrent `store_memory()` calls.
  - Spawns multiple threads calling `store_memory()` simultaneously to verify `_backup_lock` prevents race conditions.
  - Validates cache invalidation and backup timestamp consistency.

- test_deletion_fix.py
  - Covers: Proper cleanup of Chroma summary embeddings when deleting memories.
  - Specifically tests the fix for the deletion bug where summary embeddings were orphaned due to FK cascade timing.
  - Verifies that `delete_memory()` retrieves summary IDs before SQLite deletion to clean up Chroma properly.

- test_return_shape.py
  - Covers: Standardized response shapes across all MCP tools.
  - Tests that all tools return consistent dict structures with `status`, `message`, and appropriate data fields.
  - Validates success/error response formats match `format_response()` specifications.

- test_openrouter_config.py
  - Covers: OpenRouter client configuration and endpoint settings.
  - Tests that `OPENROUTER_ENDPOINT` from config is used correctly by the Summarizer.
  - Validates API key handling and custom header injection.
  - External dependency: Requires valid `OPENROUTER_API_KEY` for live API calls.

- test_update_topic_cascade_bug.py
  - Covers: Topic update cascade behavior and topic count management.
  - Tests that updating a memory's topic correctly updates topic counts (decrement old, increment new).
  - Validates ChromaDB topic document updates propagate correctly.
  - Ensures FK constraints handle topic changes without orphaning records.

**Tests requiring OPENROUTER_API_KEY:** test_core_memory_service.py, test_auxiliary_memory_service.py, test_openrouter_config.py

### Cross-cutting observations

- Environment coupling: Tests write to real `SQLITE_PATH` and `CHROMA_PATH`. Prefer isolated temporary paths to avoid polluting developer data.
- No assertions: PASS/FAIL derived from printed conditions; converting to assertions would enable CI automation.
- No fault injection: Error paths for Chroma/SQLite not exercised.

### Recommended improvements

1. **Fix and test the delete_memory bug:** Add tests to verify that Chroma summary embeddings are properly deleted when a memory is deleted (currently they are orphaned due to FK cascade ordering).
2. Migrate to pytest with fixtures for temporary DB directories and clean setup/teardown; replace prints with assertions.
3. Mock `Summarizer.generate_summary` in service tests to remove network dependency; parametrize tests for different `return_type` values and summary types.
4. Add a basic CI pipeline to run tests plus linting/type-checking.
