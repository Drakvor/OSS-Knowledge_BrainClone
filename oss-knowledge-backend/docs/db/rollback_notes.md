# Rollback Notes for V1 Migration

To revert the initial schema:

1. Drop dependent partitions if created, e.g.:
   ```sql
   DROP TABLE IF EXISTS chat_meta_2024_01;
   ```
2. Drop tables:
   ```sql
   DROP TABLE IF EXISTS chat_meta;
   DROP TABLE IF EXISTS rag_agent;
   ```
3. Remove extension when no other object requires it:
   ```sql
   DROP EXTENSION IF EXISTS "uuid-ossp";
   ```

Ensure application connections are stopped before dropping objects.
