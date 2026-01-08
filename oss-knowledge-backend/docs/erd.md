# RAG/LLM Metadata ERD

## Overview
- Stores metadata for conversations with large language models and for registered RAG/Agent components.
- All identifiers use time-sortable UUIDv7.
- Timestamps are stored as `timestamptz` in UTC and served in ISO-8601 format.
- Soft delete implemented via `deleted_at` columns.

## Entities

### rag_agent
| Column | Type | Nullable | Default | Description |
| --- | --- | --- | --- | --- |
| id | uuid | no | `uuid_generate_v7()` | PK |
| type | text | no | | RAG or Agent category |
| name | text | no | | Unique within type |
| purpose | text | yes | | Usage description |
| owner_team | text | yes | | Owning team |
| owner_user | text | yes | | Owning user |
| status | text | yes | `'active'` | Operational state |
| tags | jsonb | no | `'{}'::jsonb` | Arbitrary tags |
| created_at | timestamptz | no | `now()` | Creation time |
| updated_at | timestamptz | yes | `now()` | Last update |
| deleted_at | timestamptz | yes | | Soft delete marker |

### chat_meta
| Column | Type | Nullable | Default | Description |
| --- | --- | --- | --- | --- |
| id | uuid | no | `uuid_generate_v7()` | PK |
| session_id | text | no | | Session identifier |
| user_name | text | yes | | Raw user name (PII) |
| user_pseudonym | text | yes | | Hashed or pseudonymized user |
| rag_agent_id | uuid | yes | | FK to `rag_agent.id` |
| llm_name | text | no | | LLM model name |
| prompt_summary | text | yes | | Short prompt summary |
| liked | boolean | yes | `false` | User feedback |
| metrics | jsonb | yes | `'{}'::jsonb` | token/latency/cost etc. |
| created_at | timestamptz | no | `now()` | Conversation time |
| deleted_at | timestamptz | yes | | Soft delete marker |

## Relationships
```
rag_agent.id (1) ───< chat_meta.rag_agent_id (many)
```
A conversation may reference one RAG/Agent; each RAG/Agent can be linked to many conversation records.

## Indexing & Partitioning
- `rag_agent` : index on `(created_at)`; optional unique `(type, name)`; monthly partitioning by `created_at` if volume grows.
- `chat_meta` : composite index `(session_id, created_at)` and index on `rag_agent_id`; consider range partitioning by `created_at` (monthly) to limit 90-day hot data.

## Deletion Policy
Records are soft-deleted by setting `deleted_at`. Periodic jobs may purge rows older than retention policy.
