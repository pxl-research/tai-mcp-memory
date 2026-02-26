## Technical Background (utils)

Utility layer providing shared helpers, an OpenRouter/OpenAI API wrapper, and summarization logic used by the memory services.

Last updated: 2026-02-06 (branch: development)

### Files overview

- **init**.py

  - Re-exports `create_memory_id`, `timestamp`, and `format_response` for convenient imports.

- helpers.py

  - `create_memory_id() -> str`: Returns a UUID4 string.
  - `timestamp() -> str`: Returns current timestamp in ISO 8601 format.
  - `format_response(success: bool, message: str, data: dict | None = None) -> dict`:
    - On success: merges `data` at top level.
    - On error: nests details under `error_details` while `status` is `error`.
  - Note: Using a typed response object (e.g., dataclass/Pydantic) would ensure consistent schemas across call sites.

- open_router_client.py

  - `OpenRouterClient(OpenAI)`: Thin wrapper around the official OpenAI client configured for OpenRouter (custom base URL, headers, and defaults).
    - Constructor parameters: `api_key`, `base_url` (default `https://openrouter.ai/api/v1`), `model_name` (default `openai/gpt-4o-mini`), `tools_list`, `temperature`, `custom_headers` (adds referer/title branding by default).
    - `create_completions_stream(messages: Iterable, stream: bool = True)`: Calls `chat.completions.create(...)` with provided messages and options.
    - `set_model(model_name: str)`: Updates the default model.
  - **Configuration:** The client now uses `OPENROUTER_ENDPOINT` from config.py when instantiated via Summarizer. The hardcoded default remains for standalone usage.
  - **⚠️ Hardcoded Headers:** Client hardcodes custom headers (`HTTP-Referer: https://pxl-research.be/`, `X-Title: PXL Smart ICT`) for organizational tracking. Future enhancement: make configurable via environment variables.
  - Constants: Curated model identifiers across providers to simplify selection.
  - Considerations: Add retries/backoff and model allowlisting; consider handling OpenRouter-specific error payloads.

- summarizer.py
  - `Summarizer(api_key: str, model_name: str = 'openai/gpt-4o-mini')` uses `OpenRouterClient` to generate summaries.
  - `generate_summary(text: str, summary_type: Literal['abstractive','extractive','query_focused'] = 'abstractive', length: Literal['short','medium','detailed'] = 'medium', query: Optional[str] = None) -> Optional[str]`:
    - Builds a system prompt via `_get_system_prompt(...)`, sends a chat completion request (non-streaming), and returns the first message content.
    - Raises `ValueError` when `summary_type` is `query_focused` without a `query` (from `_get_system_prompt`).
  - Includes an `if __name__ == '__main__'` example showing various summary types and the error path.

- backup.py

  - Implements thread-safe automatic backup functionality for the memory database.

  **Key Functions:**
  - `get_last_backup_timestamp() -> Optional[datetime]`: Returns timestamp of most recent backup by parsing filenames in `BACKUP_PATH`. Returns `None` if no backups exist or path inaccessible. Uses cached value if available.
  - `should_create_backup() -> bool`: Checks if backup is due based on `BACKUP_INTERVAL_HOURS`. Compares current time against last backup timestamp. Returns `False` if backups disabled (`ENABLE_AUTO_BACKUP=false`).
  - `create_backup() -> Optional[str]`: Creates timestamped ZIP archive of `DB_PATH` directory (default: `./memory_db/`). Format: `memory_backup_YYYY-MM-DD_HH-MM-SS.zip`. Calls `cleanup_old_backups()` after successful creation. Returns backup filename on success, `None` on failure.
  - `cleanup_old_backups()`: Removes backups beyond `BACKUP_RETENTION_COUNT` (default: 10). Sorts by timestamp (oldest first) and deletes excess files.
  - `list_backups() -> List[Tuple[datetime, Path]]`: Returns sorted list of (timestamp, filepath) tuples for all backups in `BACKUP_PATH`. Useful for restore operations and status reporting.
  - `invalidate_backup_cache()`: Clears cached backup timestamp. Called internally after `create_backup()` and exposed for testing/manual cache refresh.

  **Thread Safety:** Uses module-level `threading.Lock()` (`_backup_lock`) to prevent race conditions during concurrent `store_memory()` calls. Lock protects cache reads/writes and backup creation.

  **Caching Strategy:**
  - Caches last backup timestamp (`_last_backup_cache`) to avoid filesystem stat on every `store_memory()` call
  - Cache initialized on first `get_last_backup_timestamp()` call
  - Invalidated automatically after successful backup creation
  - Cache flag (`_cache_initialized`) tracks whether cache has been populated

  **Backup Format:** ZIP archive containing entire `memory_db/` directory:
  - `memory.sqlite` - SQLite database file
  - `chroma/` - ChromaDB persistent storage directory
  - Stored in `BACKUP_PATH` directory (default: `./backups/`)

  **Configuration (from config.py):**
  - `ENABLE_AUTO_BACKUP` (bool): Enable/disable automatic backups (default: true)
  - `BACKUP_INTERVAL_HOURS` (int): Hours between automatic backups (default: 24)
  - `BACKUP_RETENTION_COUNT` (int): Number of backups to keep (default: 10)
  - `BACKUP_PATH` (str): Directory for backup storage (default: ./backups)

  **Notes:**
  - Backup creation is non-blocking; failures are logged but don't prevent memory storage
  - Timestamp parsing handles invalid filenames gracefully (skips them)
  - See `restore_memory.py` (root directory) for restore functionality

### Cross-cutting concerns

- Error handling prints to stdout; no structured logging or error types are surfaced.
- No retry/backoff for transient API failures; large inputs aren’t truncated.
- API keys are passed through to the OpenAI client; avoid printing exceptions that might leak keys.

### Recommended improvements

1. Introduce central logging and error classification; propagate exceptions with context where appropriate.
2. Add retry with exponential backoff and rate-limit handling for OpenRouter/OpenAI calls.
3. Support token budgeting (truncate inputs) and optionally streaming callbacks for incremental summaries.
