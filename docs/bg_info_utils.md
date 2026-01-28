## Technical Background (utils)

Utility layer providing shared helpers, an OpenRouter/OpenAI API wrapper, and summarization logic used by the memory services.

Last updated: 2026-01-28 (branch: development)

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
  - ⚠️ **Endpoint mismatch:** The client has a hardcoded `base_url` default of `https://openrouter.ai/api/v1`, while `config.OPENROUTER_ENDPOINT` is set to `https://api.openrouter.ai/v1` (note the different subdomain). These URLs may not be equivalent. The config value is not actually used.
  - Constants: Curated model identifiers across providers to simplify selection.
  - Considerations: Add retries/backoff and model allowlisting; consider handling OpenRouter-specific error payloads.

- summarizer.py
  - `Summarizer(api_key: str, model_name: str = 'openai/gpt-4o-mini')` uses `OpenRouterClient` to generate summaries.
  - `generate_summary(text: str, summary_type: Literal['abstractive','extractive','query_focused'] = 'abstractive', length: Literal['short','medium','detailed'] = 'medium', query: Optional[str] = None) -> Optional[str]`:
    - Builds a system prompt via `_get_system_prompt(...)`, sends a chat completion request (non-streaming), and returns the first message content.
    - Raises `ValueError` when `summary_type` is `query_focused` without a `query` (from `_get_system_prompt`).
  - Includes an `if __name__ == '__main__'` example showing various summary types and the error path.

### Cross-cutting concerns

- Error handling prints to stdout; no structured logging or error types are surfaced.
- No retry/backoff for transient API failures; large inputs aren’t truncated.
- API keys are passed through to the OpenAI client; avoid printing exceptions that might leak keys.

### Recommended improvements

1. Introduce central logging and error classification; propagate exceptions with context where appropriate.
2. Add retry with exponential backoff and rate-limit handling for OpenRouter/OpenAI calls.
3. Support token budgeting (truncate inputs) and optionally streaming callbacks for incremental summaries.
