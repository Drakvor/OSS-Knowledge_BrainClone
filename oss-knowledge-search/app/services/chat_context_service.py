import asyncpg
import os
import structlog
from typing import List, Dict, Any, Optional

logger = structlog.get_logger(__name__)

class ChatContextService:
    def __init__(self):
        self.conn_pool: Optional[asyncpg.pool.Pool] = None
        self.db_url = os.getenv("DATABASE_URL", "postgresql://oss:changeme@localhost:5432/oss_knowledge")
        logger.info(f"ChatContextService initialized with DB URL: {self.db_url}")

    async def initialize(self):
        try:
            self.conn_pool = await asyncpg.create_pool(self.db_url)
            logger.info("ChatContextService database connection pool created.")
        except Exception as e:
            logger.error(f"Failed to initialize ChatContextService: {e}")
            raise

    async def close(self):
        if self.conn_pool:
            await self.conn_pool.close()
            logger.info("ChatContextService database connection pool closed.")

    async def get_chat_context(self, session_id: str, max_turns: int = 5) -> Dict[str, Any]:
        """
        Retrieves chat history and summary for a given session ID from the PostgreSQL database.
        """
        if not self.conn_pool:
            await self.initialize()

        async with self.conn_pool.acquire() as conn:
            # Get session summary
            summary_record = await conn.fetchrow(
                "SELECT context_summary, total_tokens_used FROM chat_sessions WHERE id = $1",
                session_id
            )
            context_summary = summary_record['context_summary'] if summary_record else None
            total_tokens_used = summary_record['total_tokens_used'] if summary_record else 0

            # Get recent messages for sliding window
            # We fetch (max_turns * 2) messages because each turn has a user and an assistant message
            messages_records = await conn.fetch(
                """
                SELECT message_type, content, department_id
                FROM chat_messages
                WHERE session_id = $1
                ORDER BY turn_index DESC
                LIMIT $2
                """,
                session_id, max_turns * 2
            )

            chat_history = []
            current_department_id = None
            
            for record in reversed(messages_records): # Order chronologically
                entry = {
                    "role": record['message_type'],
                    "content": record['content']
                }
                
                # Include department_id if present
                if record['department_id'] is not None:
                    entry["department_id"] = record['department_id']
                    # Track most recent department
                    if current_department_id is None:
                        current_department_id = record['department_id']
                
                chat_history.append(entry)

            logger.debug(f"Retrieved chat context for session {session_id}: "
                         f"summary_exists={bool(context_summary)}, history_count={len(chat_history)}, "
                         f"current_department_id={current_department_id}")

            context = {
                "session_id": session_id,
                "context_summary": context_summary,
                "chat_history": chat_history,
                "total_tokens_used": total_tokens_used
            }
            
            # Add current department if found
            if current_department_id is not None:
                context["current_department_id"] = current_department_id
                # Try to get department name from database
                dept_record = await conn.fetchrow(
                    "SELECT name FROM rag_departments WHERE id = $1",
                    current_department_id
                )
                if dept_record:
                    context["current_department"] = dept_record['name']
            
            return context
