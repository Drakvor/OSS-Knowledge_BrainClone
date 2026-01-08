"""
Orchestrator Core Logic
Coordinates between services and manages chat flow
"""

import logging
import os
from typing import Dict, Any, Optional
from app.clients.context_manager_client import ContextManagerClient
from app.clients.intent_classifier_client import IntentClassifierClient
from app.clients.search_client import SearchClient
from app.clients.task_planner_client import TaskPlannerClient
from app.clients.backend_client import BackendClient

logger = logging.getLogger(__name__)


class Orchestrator:
    """
    Main orchestrator class for coordinating services
    
    Responsibilities:
    - Chat context building
    - Service coordination
    - Routing decisions
    - Streaming management
    """
    
    def __init__(self):
        """Initialize orchestrator"""
        logger.info("Initializing Orchestrator")
        # Service clients
        self.context_manager_client = ContextManagerClient()
        self.intent_classifier_client = IntentClassifierClient()  # Phase 10
        self.search_client = SearchClient()  # Phase 10
        self.task_planner_client = TaskPlannerClient()  # Phase 11
        self.backend_client = BackendClient()  # Phase 12
        
        # Configuration
        use_task_planner_env = os.getenv("USE_TASK_PLANNER", "true")  # Default to true
        self.use_task_planner = use_task_planner_env.lower() == "true"
        logger.info(f"Task Planner enabled: {self.use_task_planner} (from USE_TASK_PLANNER={use_task_planner_env})")
    
    async def build_chat_context(
        self,
        session_id: str,
        user_id: str,
        current_query: str,
        chat_history_limit: int = 6,
        user_memory_limit: int = 3,
        session_memory_limit: int = 5,
        attachments: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Build chat context using Context Manager service.
        
        Phase 9: Context Manager Integration
        
        Args:
            session_id: Chat session identifier
            user_id: User identifier
            current_query: Current user query
            chat_history_limit: Number of recent messages (default: 6 = 3 turns)
            user_memory_limit: Number of user memories to retrieve
            session_memory_limit: Number of session memories to retrieve
            attachments: File attachments
            
        Returns:
            Dictionary containing enriched chat context with:
            - chat_history: Recent messages (sliding window)
            - context_summary: Session summary if available
            - user_memories: User-level memories from mem0
            - session_memories: Session-level memories from mem0
            - attachments_text: Extracted text from attachments
        """
        logger.debug(f"Building chat context for session {session_id}, user {user_id}")
        
        try:
            context = await self.context_manager_client.build_context(
                session_id=session_id,
                user_id=user_id,
                current_query=current_query,
                chat_history_limit=chat_history_limit,
                user_memory_limit=user_memory_limit,
                session_memory_limit=session_memory_limit,
                attachments=attachments
            )
            
            logger.debug(f"Context built successfully - {len(context.get('chat_history', []))} messages, "
                        f"{len(context.get('user_memories', []))} user memories, "
                        f"{len(context.get('session_memories', []))} session memories")
            
            return context
            
        except Exception as e:
            logger.error(f"Failed to build context: {e}")
            # Return minimal context on error
            return {
                "session_id": session_id,
                "user_id": user_id,
                "current_query": current_query,
                "chat_history": [],
                "context_summary": None,
                "user_memories": [],
                "session_memories": [],
                "attachments_text": []
            }
    
    async def save_memory(
        self,
        message: str,
        response: str,
        user_id: str,
        session_id: str,
        is_important: bool = False
    ) -> bool:
        """
        Save conversation to memory via Context Manager
        
        Phase 9: Context Manager Integration
        
        Args:
            message: User message
            response: Assistant response
            user_id: User identifier
            session_id: Session identifier
            is_important: Whether this is an important conversation
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Combine message and response for memory storage
            memory_text = f"User: {message}\nAssistant: {response}"
            
            success = await self.context_manager_client.add_memory(
                message=memory_text,
                user_id=user_id,
                session_id=session_id,
                memory_type="conversation_context",
                is_important=is_important
            )
            
            if success:
                logger.debug(f"Memory saved successfully for session {session_id}")
            else:
                logger.warning(f"Failed to save memory for session {session_id}")
            
            return success
        except Exception as e:
            logger.error(f"Error saving memory: {e}")
            return False
    
    async def orchestrate_chat(
        self,
        message: str,
        session_id: str,
        user_id: str,
        collection: str = "general",
        chat_context: Optional[Dict[str, Any]] = None,
        attachments: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Main orchestration method for chat requests.
        
        Phase 9-10: Chain pattern implementation
        O → CM → O → IC → O → (SS/TP/CM) → O → CM → O
        
        Args:
            message: User message
            session_id: Chat session identifier
            user_id: User identifier
            collection: Collection for RAG search
            chat_context: Optional pre-built chat context
            attachments: Optional file attachments
            
        Returns:
            Response dictionary with response, intent, and metadata
        """
        logger.info(f"Orchestrating chat request: session_id={session_id}, message_length={len(message)}")
        
        try:
            # Step 1: Build chat context via Context Manager
            if chat_context is None:
                chat_context = await self.build_chat_context(
                    session_id=session_id,
                    user_id=user_id,
                    current_query=message,
                    attachments=attachments
                )
            
            # Step 2: Classify intent via Intent Classifier
            intent_result = await self.intent_classifier_client.classify_intent(
                message=message,
                chat_context=chat_context
            )
            intent = intent_result.get("intent", "UNKNOWN")
            reasoning = intent_result.get("reasoning", "")
            
            logger.info(f"Intent classified as: {intent} - {reasoning}")
            
            # Step 3: Route based on intent
            response_text = ""
            sources = []
            metadata = {"intent": intent, "reasoning": reasoning}
            
            if intent == "CASUAL":
                # Direct response without DB calls
                response_text = await self._handle_casual_intent(message, chat_context)
                
            elif intent == "COMPLEX":
                # Route to Task Planner or Search Server based on config
                if self.use_task_planner:
                    # Use Task Planner for complex multi-step queries
                    plan = await self.task_planner_client.create_plan(
                        query=message,
                        user_id=int(user_id) if user_id and str(user_id).isdigit() else None,
                        session_id=session_id,
                        chat_context=chat_context,
                        collection=collection
                    )
                    
                    execution_result = await self.task_planner_client.execute_plan(plan)
                    
                    final_result = execution_result.get("final_result", {})
                    response_text = final_result.get("response", "Task execution completed.")
                    sources = final_result.get("sources", [])
                    metadata.update({
                        "plan_id": execution_result.get("plan_id"),
                        "tasks_count": len(execution_result.get("tasks", [])),
                        "method": "task_planner"
                    })
                else:
                    # Use Search Server for direct RAG
                    search_result = await self.search_client.search_and_generate(
                        query=message,
                        collection=collection,
                        chat_context=chat_context,
                        user_id=int(user_id) if user_id and str(user_id).isdigit() else None,
                        session_id=session_id
                    )
                    response_text = search_result.get("response", "")
                    sources = search_result.get("sources", [])
                    metadata.update({
                        "search_results_count": len(search_result.get("search_results", [])),
                        "collection": collection,
                        "method": "search_server"
                    })
                
            elif intent == "CONTEXT":
                # Route to Context Manager for context-based response
                response_text = await self._handle_context_intent(message, chat_context)
                
            else:  # UNKNOWN
                # Fallback response
                response_text = await self._handle_unknown_intent(message, chat_context)
            
            # Step 4: Save memory via Context Manager
            await self.save_memory(
                message=message,
                response=response_text,
                user_id=user_id,
                session_id=session_id,
                is_important=(intent == "COMPLEX")  # Mark complex queries as important
            )
            
            # Step 5: Save messages to Backend
            try:
                await self.backend_client.save_message(
                    session_id=session_id,
                    role="user",
                    content=message
                )
                await self.backend_client.save_message(
                    session_id=session_id,
                    role="assistant",
                    content=response_text
                )
            except Exception as e:
                logger.warning(f"Failed to save messages to backend: {e}")
                # Continue even if backend save fails
            
            return {
                "response": response_text,
                "intent": intent,
                "reasoning": reasoning,
                "sources": sources,
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"Orchestration failed: {e}", exc_info=True)
            return {
                "response": f"Sorry, I encountered an error: {str(e)}",
                "intent": "UNKNOWN",
                "reasoning": f"Error during orchestration: {str(e)}",
                "sources": [],
                "metadata": {"error": str(e)}
            }
    
    # Simplified intent handlers - using constants and inline logic
    CASUAL_RESPONSES = {
        "안녕": "안녕하세요! 무엇을 도와드릴까요?",
        "hello": "Hello! How can I help you?",
        "hi": "Hi! What can I do for you?",
        "고마워": "천만에요! 다른 도움이 필요하시면 언제든 말씀해주세요.",
        "thanks": "You're welcome! Let me know if you need anything else."
    }
    
    DEFAULT_CASUAL_RESPONSE = "안녕하세요! 무엇을 도와드릴까요?"
    DEFAULT_CONTEXT_RESPONSE = "이전 대화 내용을 찾을 수 없습니다. 새로운 질문을 해주시면 도와드리겠습니다."
    DEFAULT_UNKNOWN_RESPONSE = "죄송합니다. 질문을 명확히 이해하지 못했습니다. 다시 말씀해주시거나 다른 방식으로 질문해주시면 도와드리겠습니다."
    
    async def _handle_casual_intent(self, message: str, chat_context: Dict[str, Any]) -> str:
        """Handle CASUAL intent - simple greetings and casual conversation"""
        message_lower = message.lower().strip()
        for key, response in self.CASUAL_RESPONSES.items():
            if key in message_lower:
                return response
        return self.DEFAULT_CASUAL_RESPONSE
    
    async def _handle_context_intent(self, message: str, chat_context: Dict[str, Any]) -> str:
        """Handle CONTEXT intent - queries about past conversation"""
        chat_history = chat_context.get("chat_history", [])
        if chat_history:
            recent_context = "\n".join([
                f"{msg.get('role', 'user')}: {msg.get('content', '')}" 
                for msg in chat_history[-3:]
            ])
            return f"이전 대화 내용을 참고하면:\n\n{recent_context}\n\n추가로 궁금한 점이 있으시면 말씀해주세요."
        
        user_memories = chat_context.get("user_memories", [])
        session_memories = chat_context.get("session_memories", [])
        if user_memories or session_memories:
            return "이전 대화 내용을 찾았습니다. 구체적으로 어떤 부분에 대해 알고 싶으신가요?"
        
        return self.DEFAULT_CONTEXT_RESPONSE
    
    async def _handle_unknown_intent(self, message: str, chat_context: Dict[str, Any]) -> str:
        """Handle UNKNOWN intent - unclear queries"""
        return self.DEFAULT_UNKNOWN_RESPONSE
    
    async def orchestrate_chat_stream(
        self,
        message: str,
        session_id: str,
        user_id: str,
        collection: str = "general",
        chat_context: Optional[Dict[str, Any]] = None,
        attachments: Optional[list] = None
    ):
        """
        Streaming version of orchestrate_chat that yields SSE events.
        
        Yields events:
        - intent: Intent classification result
        - plan_created: Task plan created
        - task_status: Task status update
        - task_result: Task execution result
        - response_chunk: Final response chunk
        - done: Stream complete
        
        Args:
            message: User message
            session_id: Chat session identifier
            user_id: User identifier
            collection: Collection for RAG search
            chat_context: Optional pre-built chat context
            attachments: Optional file attachments
            
        Yields:
            Event dictionaries with type and data
        """
        import asyncio
        import json
        
        logger.info(f"Orchestrating chat stream: session_id={session_id}, message_length={len(message)}")
        
        try:
            # Step 1: Build chat context via Context Manager
            if chat_context is None:
                chat_context = await self.build_chat_context(
                    session_id=session_id,
                    user_id=user_id,
                    current_query=message,
                    attachments=attachments
                )
            
            # Step 2: Classify intent via Intent Classifier
            intent_result = await self.intent_classifier_client.classify_intent(
                message=message,
                chat_context=chat_context
            )
            intent = intent_result.get("intent", "UNKNOWN")
            reasoning = intent_result.get("reasoning", "")
            
            # Yield intent event
            yield {
                "type": "intent",
                "data": {
                    "intent": intent,
                    "reasoning": reasoning
                }
            }
            
            logger.info(f"Intent classified as: {intent} - {reasoning}")
            
            # Step 3: Route based on intent
            response_text = ""
            sources = []
            metadata = {"intent": intent, "reasoning": reasoning}
            plan_id = None
            
            if intent == "CASUAL":
                # Direct response without DB calls
                response_text = await self._handle_casual_intent(message, chat_context)
                
            elif intent == "COMPLEX":
                # Route to Task Planner or Search Server based on config
                if self.use_task_planner:
                    # Use Task Planner for complex multi-step queries
                    plan = await self.task_planner_client.create_plan(
                        query=message,
                        user_id=int(user_id) if user_id and str(user_id).isdigit() else None,
                        session_id=session_id,
                        chat_context=chat_context,
                        collection=collection
                    )
                    
                    plan_id = plan.get("plan_id")
                    tasks = plan.get("tasks", [])
                    
                    # Yield plan_created event
                    yield {
                        "type": "plan_created",
                        "data": {
                            "plan_id": plan_id,
                            "tasks": tasks
                        }
                    }
                    
                    # Execute plan and yield task status updates
                    # Poll task status during execution
                    execution_result = None
                    async for event in self._execute_plan_with_streaming(plan, plan_id):
                        # Yield task status events
                        if event.get("type") in ["task_status", "task_result"]:
                            yield event
                        # Check if event contains execution result
                        elif event.get("type") == "execution_complete":
                            execution_result = event.get("data")
                            # Don't yield this event, it's internal
                    
                    # If execution result not received, get it directly (fallback)
                    if execution_result is None:
                        execution_result = await self.task_planner_client.execute_plan(plan)
                    
                    final_result = execution_result.get("final_result", {})
                    response_text = final_result.get("response", "Task execution completed.")
                    sources = final_result.get("sources", [])
                    metadata.update({
                        "plan_id": plan_id,
                        "tasks_count": len(execution_result.get("tasks", [])),
                        "method": "task_planner"
                    })
                else:
                    # Use Search Server for direct RAG
                    search_result = await self.search_client.search_and_generate(
                        query=message,
                        collection=collection,
                        chat_context=chat_context,
                        user_id=int(user_id) if user_id and str(user_id).isdigit() else None,
                        session_id=session_id
                    )
                    response_text = search_result.get("response", "")
                    sources = search_result.get("sources", [])
                    metadata.update({
                        "search_results_count": len(search_result.get("search_results", [])),
                        "collection": collection,
                        "method": "search_server"
                    })
                
            elif intent == "CONTEXT":
                # Route to Context Manager for context-based response
                response_text = await self._handle_context_intent(message, chat_context)
                
            else:  # UNKNOWN
                # Fallback response
                response_text = await self._handle_unknown_intent(message, chat_context)
            
            # Step 4: Stream response chunks
            if response_text:
                # Split response into chunks for streaming
                words = response_text.split()
                for i, word in enumerate(words):
                    chunk = word + (" " if i < len(words) - 1 else "")
                    yield {
                        "type": "response_chunk",
                        "data": {
                            "chunk": chunk
                        }
                    }
                    # Small delay for smooth streaming
                    await asyncio.sleep(0.05)
            
            # Step 5: Save memory via Context Manager (non-blocking)
            asyncio.create_task(self.save_memory(
                message=message,
                response=response_text,
                user_id=user_id,
                session_id=session_id,
                is_important=(intent == "COMPLEX")
            ))
            
            # Step 6: Save messages to Backend (non-blocking)
            asyncio.create_task(self._save_messages_async(
                session_id=session_id,
                message=message,
                response=response_text
            ))
            
            # Yield done event
            yield {
                "type": "done",
                "data": {
                    "response": response_text,
                    "metadata": metadata
                }
            }
            
        except Exception as e:
            logger.error(f"Streaming orchestration failed: {e}", exc_info=True)
            yield {
                "type": "error",
                "data": {
                    "error": str(e)
                }
            }
    
    async def _execute_plan_with_streaming(
        self,
        plan: Dict[str, Any],
        plan_id: str
    ):
        """
        Execute plan and yield task status updates.
        
        Args:
            plan: Plan dictionary
            plan_id: Plan ID
            
        Yields:
            Event dictionaries with type and data
        """
        import asyncio
        
        # Start execution in background
        execution_task = asyncio.create_task(
            self.task_planner_client.execute_plan(plan)
        )
        
        # Poll task status while execution is running
        tasks = plan.get("tasks", [])
        task_ids = [task.get("task_id") for task in tasks]
        completed_tasks = set()
        in_progress_tasks = set()
        
        while not execution_task.done():
            # Poll task status
            for task_id in task_ids:
                if task_id not in completed_tasks:
                    try:
                        task_status = await self.task_planner_client._request(
                            "GET",
                            f"/tasks/{task_id}",
                            raise_on_error=False
                        )
                        if task_status:
                            status = task_status.get("status")
                            # Handle both "in_progress" and "running" status
                            if status in ["in_progress", "running"] and task_id not in in_progress_tasks:
                                in_progress_tasks.add(task_id)
                                # Yield task_status event
                                yield {
                                    "type": "task_status",
                                    "data": {
                                        "task_id": task_id,
                                        "status": "in_progress",
                                        "description": task_status.get("description", "")
                                    }
                                }
                            elif status == "completed" and task_id not in completed_tasks:
                                completed_tasks.add(task_id)
                                if task_id in in_progress_tasks:
                                    in_progress_tasks.remove(task_id)
                                
                                # Yield task_result event
                                yield {
                                    "type": "task_result",
                                    "data": {
                                        "task_id": task_id,
                                        "result": task_status.get("result"),
                                        "content": self._format_task_result(task_status)
                                    }
                                }
                                # Yield task_status completed
                                yield {
                                    "type": "task_status",
                                    "data": {
                                        "task_id": task_id,
                                        "status": "completed",
                                        "description": task_status.get("description", "")
                                    }
                                }
                            elif status == "failed" and task_id not in completed_tasks:
                                completed_tasks.add(task_id)
                                if task_id in in_progress_tasks:
                                    in_progress_tasks.remove(task_id)
                                yield {
                                    "type": "task_status",
                                    "data": {
                                        "task_id": task_id,
                                        "status": "failed",
                                        "description": task_status.get("description", ""),
                                        "error": task_status.get("error")
                                    }
                                }
                    except Exception as e:
                        logger.debug(f"Error polling task {task_id}: {e}")
            
            await asyncio.sleep(0.2)  # Poll every 200ms for faster updates
        
        # Wait for execution to complete and yield final result
        execution_result = await execution_task
        
        # Yield execution complete event
        yield {
            "type": "execution_complete",
            "data": execution_result
        }
    
    def _format_task_result(self, task_status: Dict[str, Any]) -> str:
        """Format task result for display"""
        result = task_status.get("result")
        if not result:
            return ""
        
        task_type = task_status.get("task_type", "")
        if task_type == "RETRIEVE":
            if isinstance(result, dict):
                content = result.get("content", "")
                if content:
                    return f"검색 결과: {content[:200]}..." if len(content) > 200 else f"검색 결과: {content}"
        elif task_type == "ANALYZE":
            if isinstance(result, dict):
                analysis = result.get("analysis", "")
                if analysis:
                    return f"분석 결과: {analysis[:200]}..." if len(analysis) > 200 else f"분석 결과: {analysis}"
        elif task_type == "GENERATE":
            if isinstance(result, dict):
                response = result.get("response", "")
                if response:
                    return f"생성 결과: {response[:200]}..." if len(response) > 200 else f"생성 결과: {response}"
        
        return str(result)[:200] if result else ""
    
    async def _save_messages_async(self, session_id: str, message: str, response: str):
        """Save messages to backend asynchronously"""
        try:
            await self.backend_client.save_message(
                session_id=session_id,
                role="user",
                content=message
            )
            await self.backend_client.save_message(
                session_id=session_id,
                role="assistant",
                content=response
            )
        except Exception as e:
            logger.warning(f"Failed to save messages to backend: {e}")

