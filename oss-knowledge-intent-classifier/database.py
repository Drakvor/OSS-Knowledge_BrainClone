"""
Database connection and chat history management for Intent Classifier
"""

import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Database manager for chat history operations"""
    
    def __init__(self):
        self.connection = None
        self.engine = None
        self.session_factory = None
        self._setup_connection()
    
    def _setup_connection(self):
        """Setup database connection"""
        try:
            # Database connection parameters
            db_url = os.getenv('DB_URL', 'postgresql://oss:changeme@localhost:5432/oss_knowledge')
            db_username = os.getenv('DB_USERNAME', 'oss')
            db_password = os.getenv('DB_PASSWORD', 'changeme')
            db_host = os.getenv('DB_HOST', 'localhost')
            db_port = os.getenv('DB_PORT', '5432')
            db_name = os.getenv('DB_NAME', 'oss_knowledge')
            
            # Create connection string
            connection_string = f"postgresql://{db_username}:{db_password}@{db_host}:{db_port}/{db_name}"
            
            # Setup SQLAlchemy engine
            self.engine = create_engine(connection_string, echo=False)
            self.session_factory = sessionmaker(bind=self.engine)
            
            # Test connection
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            logger.info("Database connection established successfully")
            
        except Exception as e:
            logger.error(f"Failed to setup database connection: {e}")
            raise
    
    def get_chat_history(self, session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get chat history for a session"""
        try:
            with self.engine.connect() as conn:
                # Query chat history from the database
                query = text("""
                    SELECT 
                        id,
                        session_id,
                        turn_index,
                        message_type,
                        content,
                        token_count,
                        department_id,
                        metadata,
                        parent_message_id,
                        status,
                        created_at
                    FROM chat_messages 
                    WHERE session_id = :session_id 
                    ORDER BY turn_index DESC 
                    LIMIT :limit
                """)
                
                result = conn.execute(query, {"session_id": session_id, "limit": limit})
                rows = result.fetchall()
                
                # Convert to list of dictionaries
                chat_history = []
                for row in rows:
                    chat_history.append({
                        "id": row.id,
                        "session_id": row.session_id,
                        "turn_index": row.turn_index,
                        "message_type": row.message_type,
                        "content": row.content,
                        "token_count": row.token_count,
                        "department_id": row.department_id,
                        "metadata": row.metadata,
                        "parent_message_id": row.parent_message_id,
                        "status": row.status,
                        "created_at": row.created_at.isoformat() if row.created_at else None
                    })
                
                logger.info(f"Retrieved {len(chat_history)} chat history records for session {session_id}")
                return chat_history
                
        except Exception as e:
            logger.error(f"Failed to get chat history for session {session_id}: {e}")
            return []
    
    def save_chat_message(self, session_id: str, user_id: str, message: str, 
                         response: str, intent: str) -> bool:
        """Save chat message to database"""
        try:
            with self.engine.connect() as conn:
                # First, get the next turn_index for this session
                turn_query = text("""
                    SELECT COALESCE(MAX(turn_index), 0) + 1 as next_turn
                    FROM chat_messages 
                    WHERE session_id = :session_id
                """)
                turn_result = conn.execute(turn_query, {"session_id": session_id})
                next_turn = turn_result.fetchone().next_turn
                
                # Insert user message
                user_query = text("""
                    INSERT INTO chat_messages 
                    (session_id, turn_index, message_type, content, created_at)
                    VALUES (:session_id, :turn_index, :message_type, :content, :created_at)
                """)
                
                conn.execute(user_query, {
                    "session_id": session_id,
                    "turn_index": next_turn,
                    "message_type": "user",
                    "content": message,
                    "created_at": datetime.utcnow()
                })
                
                # Insert assistant response
                assistant_query = text("""
                    INSERT INTO chat_messages 
                    (session_id, turn_index, message_type, content, metadata, created_at)
                    VALUES (:session_id, :turn_index, :message_type, :content, :metadata, :created_at)
                """)
                
                metadata = {"intent": intent}
                
                conn.execute(assistant_query, {
                    "session_id": session_id,
                    "turn_index": next_turn + 1,
                    "message_type": "assistant",
                    "content": response,
                    "metadata": metadata,
                    "created_at": datetime.utcnow()
                })
                
                conn.commit()
                
                logger.info(f"Saved chat message for session {session_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to save chat message for session {session_id}: {e}")
            return False
    
    def close(self):
        """Close database connection"""
        if self.engine:
            self.engine.dispose()
            logger.info("Database connection closed")

# Global database manager instance
db_manager = DatabaseManager()
