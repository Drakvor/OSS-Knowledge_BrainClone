# ERD Design Notes

## Keys & Time
- Use `uuid` columns populated with `uuid_generate_v7()` (extension required) for time-ordered identifiers.
- All time fields use `timestamptz` and should be stored in UTC. Application layer formats ISO-8601.

## Table Rationale
### rag_agent
- Captures metadata for RAG or Agent components supplied by the main system.
- `tags` uses `jsonb` to allow flexible tagging without schema changes.
- `status` defaults to `active` but can track lifecycle (`inactive`, `deprecated`).
- `deleted_at` enables soft delete; background jobs may hard-delete after retention.

### chat_meta
- Stores per-session conversation summaries with an optional reference to `rag_agent`.
- `user_pseudonym` allows storage of hashed user identifiers when `user_name` must be masked.
- `metrics` keeps variable statistics such as token usage, latency, or cost without table alteration.
- Index on `(session_id, created_at)` optimizes recent 90-day lookups; additional index on `rag_agent_id` enables joins.

## Partitioning
- Both tables may employ monthly range partitioning on `created_at` to keep only recent partitions in hot storage.
- Archival partitions older than 90 days can be moved to cheaper storage or pruned.

## Constraints & Security
- Foreign key `chat_meta.rag_agent_id` references `rag_agent.id` with `ON UPDATE CASCADE` and `ON DELETE SET NULL`.
- Application should use parameterized SQL to prevent injection.
- Store only pseudonymized user identifiers when possible to reduce PII exposure.
