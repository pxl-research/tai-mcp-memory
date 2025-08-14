# Database Schema Documentation

Comprehensive view of the SQLite + Chroma hybrid storage model. This document focuses on the **SQLite** relational schema (authoritative structured store) and conceptual linkage to **ChromaDB** collections.

## Entity Relationship (SQLite)

```mermaid
erDiagram
    TOPICS ||--o{ MEMORY_ITEMS : contains
    MEMORY_ITEMS ||--o{ SUMMARIES : has

    TOPICS {
        TEXT name PK
        TEXT description
        INTEGER item_count
        TEXT created_at
        TEXT updated_at
    }

    MEMORY_ITEMS {
        TEXT id PK
        TEXT content
        TEXT topic_name FK -> TOPICS.name
        TEXT tags  // comma-separated list
        TEXT created_at
        TEXT updated_at
        INTEGER version
    }

    SUMMARIES {
        TEXT id PK
        TEXT memory_id FK -> MEMORY_ITEMS.id
        TEXT summary_type
        TEXT summary_text
        TEXT created_at
        TEXT updated_at
    }
```

## Table Specifications

### 1. `topics`

| Column        | Type    | Constraints    | Description                                                    |
| ------------- | ------- | -------------- | -------------------------------------------------------------- |
| `name`        | TEXT    | PRIMARY KEY    | Unique topic identifier.                                       |
| `description` | TEXT    | NULLABLE       | (Currently unused placeholder) Optional human description.     |
| `item_count`  | INTEGER | DEFAULT 0      | Count of memory items referencing the topic. Updated manually. |
| `created_at`  | TEXT    | NOT NULL (ISO) | Creation timestamp.                                            |
| `updated_at`  | TEXT    | NOT NULL (ISO) | Last modification timestamp.                                   |

Notes:

- No explicit index beyond PK (implicit). Consider adding index on `updated_at` for recent-topic queries.
- `item_count` integrity depends on correct increment/decrement logic (currently decrement bug in `_remove_from_topic`).

### 2. `memory_items`

| Column       | Type    | Constraints                 | Description                                 |
| ------------ | ------- | --------------------------- | ------------------------------------------- |
| `id`         | TEXT    | PRIMARY KEY                 | UUID for the memory record.                 |
| `content`    | TEXT    | NOT NULL                    | Full original stored content.               |
| `topic_name` | TEXT    | NOT NULL, FK -> topics.name | Topic association (ON DELETE CASCADE).      |
| `tags`       | TEXT    | NULLABLE                    | Comma-separated list of tags (no escaping). |
| `created_at` | TEXT    | NOT NULL (ISO)              | Creation timestamp.                         |
| `updated_at` | TEXT    | NOT NULL (ISO)              | Last update timestamp.                      |
| `version`    | INTEGER | DEFAULT 1                   | Incremented on each update.                 |

Notes:

- Potential future improvements: full-text index (FTS5) for hybrid lexical + semantic search, normalized tag table.
- Referential integrity relies on enabling `PRAGMA foreign_keys=ON` (not enforced currently in code).

### 3. `summaries`

| Column         | Type | Constraints                     | Description                                  |
| -------------- | ---- | ------------------------------- | -------------------------------------------- |
| `id`           | TEXT | PRIMARY KEY                     | UUID for summary entry.                      |
| `memory_id`    | TEXT | NOT NULL, FK -> memory_items.id | Parent memory reference (ON DELETE CASCADE). |
| `summary_type` | TEXT | NOT NULL                        | Classification (e.g. `abstractive_medium`).  |
| `summary_text` | TEXT | NOT NULL                        | Generated summary content.                   |
| `created_at`   | TEXT | NOT NULL (ISO)                  | Creation timestamp.                          |
| `updated_at`   | TEXT | NOT NULL (ISO)                  | Last update timestamp.                       |

Notes:

- No uniqueness constraint on `(memory_id, summary_type)` — duplicates possible.
- Add composite unique index if only one summary per type desired.

## ChromaDB Collections (Conceptual)

While not relational, Chroma stores metadata alongside embeddings:

| Collection     | Document Source             | Key Metadata Fields                  |
| -------------- | --------------------------- | ------------------------------------ |
| `memory_items` | Full memory `content`       | `id`, `topic`, `tags`, timestamps    |
| `summaries`    | Generated `summary_text`    | `memory_id`, `summary_type`, `topic` |
| `topics`       | Synthetic topic description | `name`, `tags`                       |

Alignment Rules:

- SQLite `memory_items.id` ↔ Chroma `memory_items` `id` field.
- SQLite `summaries.id` ↔ Chroma `summaries` `id` field.
- SQLite `summaries.memory_id` ↔ Chroma summary metadata `memory_id`.
- Topics mirrored by name.

## Data Flow Summary

1. Insert memory → row in `memory_items` → embedding in Chroma `memory_items`.
2. Auto summary → row in `summaries` → embedding in Chroma `summaries`.
3. Retrieval → semantic search summaries → hydrate memory from SQLite.
4. Update memory → SQLite row updated (version++) → Chroma document updated → summary regenerated (if content changed).
5. Delete memory → cascade delete summaries (SQLite) → explicit delete memory + summary embeddings (Chroma).

## Integrity & Risk Notes

- Missing foreign key pragma may allow orphan rows if not enforced manually.
- Dual-write inconsistency risk (no transactional coordination) — introduce reconciliation or a write-ahead queue.
- Tag serialization brittle (commas in tags break splitting). Consider JSON.
- `_remove_from_topic` bug causes incorrect `item_count` maintenance.

## Suggested Enhancements

| Area                  | Recommendation                                                                               |
| --------------------- | -------------------------------------------------------------------------------------------- |
| Referential Integrity | Enable `PRAGMA foreign_keys=ON` on each connection.                                          |
| Topic Count Logic     | Fix decrement bug; add constraint or trigger.                                                |
| Tags Model            | Store as JSON or separate table (`memory_tags(memory_id, tag)`).                             |
| Summary Uniqueness    | Add `UNIQUE(memory_id, summary_type)` if one-per-type.                                       |
| Observability         | Add change log table for audit/version diffs.                                                |
| Performance           | Add indices on `topic_name`, `created_at`; consider FTS5 virtual table for lexical fallback. |
| Consistency           | Implement reconciliation script comparing SQLite IDs vs Chroma IDs.                          |

## Quick Reference SQL

(For indexing & integrity improvements)

```sql
-- Enable foreign keys
PRAGMA foreign_keys = ON;

-- Add uniqueness on memory_id + summary_type (optional)
CREATE UNIQUE INDEX IF NOT EXISTS idx_summaries_memory_type ON summaries(memory_id, summary_type);

-- Index for topic-based queries
CREATE INDEX IF NOT EXISTS idx_memory_items_topic ON memory_items(topic_name);

-- Full text search (future)
-- CREATE VIRTUAL TABLE memory_items_fts USING fts5(content, content='memory_items', content_rowid='rowid');
```

_Generated on: 2025-08-14_
