"""
Task planning and decomposition logic
"""

import logging
import os
import json
from typing import Dict, Any, Optional, List
from app.utils.azure_client import create_azure_openai_client
from app.models.task_models import Plan, Task, TaskParameters

logger = logging.getLogger(__name__)

class TaskPlanner:
    """Handles task planning and decomposition"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.client = None
        self.initialized = False
        self._initialize_client()
        self.logger.info("Task Planner initialized")
    
    def _initialize_client(self):
        """Initialize Azure OpenAI client using shared factory"""
        try:
            self.client = create_azure_openai_client()
            self.initialized = True
            logger.info("Azure OpenAI client initialized for TaskPlanner")
        except Exception as e:
            logger.error(f"Failed to initialize Azure OpenAI client: {e}")
            # Don't raise - will handle gracefully
    
    def _build_decomposition_prompt(self, query: str, chat_context: Optional[Dict[str, Any]] = None, collection: Optional[str] = None) -> str:
        """Build prompt for task decomposition"""
        collection_info = f"\nTarget Collection: \"{collection}\"" if collection else "\nTarget Collection: \"general\" (default)"
        prompt = f"""You are a task planner for a RAG system. Decompose the user's query into a series of tasks.

Task Types:
- RETRIEVE: Search and retrieve information from vector database (Qdrant) or via Search Server
- ANALYZE: Process, compare, or analyze retrieved information
- GENERATE: Generate final response based on analysis

User Query: "{query}"{collection_info}

Important:
- Use the Target Collection specified above for RETRIEVE tasks
- Do NOT use "documents" or "general" unless that is the actual target collection
- The collection parameter in RETRIEVE task parameters must match the Target Collection

Decompose this query into tasks. Each task should have:
- task_id: Unique identifier (e.g., "task_1", "task_2")
- task_type: RETRIEVE, ANALYZE, or GENERATE
- description: What this task does
- parameters: JSON object with task-specific parameters
  - For RETRIEVE: {{"search_query": "...", "collection": "...", "limit": 5}}
  - For ANALYZE: {{"analysis_type": "...", "input_tasks": ["task_1", "task_2"]}}
  - For GENERATE: {{"response_type": "...", "input_task": "task_3"}}
- dependencies: List of task_ids that must complete before this task (empty list [] if no dependencies)

Important:
- RETRIEVE tasks can run in parallel (no dependencies on each other)
- ANALYZE tasks depend on their input RETRIEVE tasks
- GENERATE tasks depend on ANALYZE tasks (or directly on RETRIEVE if no analysis needed)
- Always end with a GENERATE task for the final response

Respond with ONLY valid JSON in this format:
{{
  "tasks": [
    {{
      "task_id": "task_1",
      "task_type": "RETRIEVE",
      "description": "Retrieve information about X",
      "parameters": {{"search_query": "X", "collection": "{collection or "general"}", "limit": 5}},
      "dependencies": []
    }},
    {{
      "task_id": "task_2",
      "task_type": "ANALYZE",
      "description": "Analyze the retrieved information",
      "parameters": {{"analysis_type": "comparison", "input_tasks": ["task_1"]}},
      "dependencies": ["task_1"]
    }},
    {{
      "task_id": "task_3",
      "task_type": "GENERATE",
      "description": "Generate final response",
      "parameters": {{"response_type": "comprehensive", "input_task": "task_2"}},
      "dependencies": ["task_2"]
    }}
  ]
}}
"""
        
        if chat_context and chat_context.get("chat_history"):
            prompt += f"\n\nChat History (for context):\n"
            for msg in chat_context.get("chat_history", [])[-3:]:
                prompt += f"- {msg.get('role', 'user')}: {msg.get('content', '')[:100]}\n"
        
        return prompt
    
    async def create_plan(
        self,
        query: str,
        user_id: Optional[int] = None,
        session_id: Optional[str] = None,
        chat_context: Optional[Dict[str, Any]] = None,
        collection: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a task plan from a query by decomposing it into tasks with dependencies.
        """
        self.logger.debug(f"Creating plan for query: {query[:50]}, collection: {collection}")
        
        if not self.initialized or not self.client:
            self.logger.error("Azure OpenAI client not initialized")
            raise Exception("Task Planner not properly initialized")
        
        try:
            # Build decomposition prompt
            prompt = self._build_decomposition_prompt(query, chat_context, collection)
            
            # Call Azure OpenAI for task decomposition
            deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4.1-mini")
            response = self.client.chat.completions.create(
                model=deployment,
                messages=[
                    {"role": "system", "content": "You are a task planner. Respond with ONLY valid JSON in the specified format."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            # Parse response
            content = response.choices[0].message.content
            try:
                plan_data = json.loads(content)
            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse JSON response: {e}")
                raise ValueError(f"Invalid JSON response from LLM: {e}")
            
            # Create Plan object with tasks
            tasks = []
            for task_data in plan_data.get("tasks", []):
                # Create TaskParameters
                params = TaskParameters(**task_data.get("parameters", {}))
                
                # Create Task
                task = Task(
                    task_id=task_data.get("task_id", f"task_{len(tasks) + 1}"),
                    task_type=task_data.get("task_type", "RETRIEVE"),
                    description=task_data.get("description", ""),
                    parameters=params,
                    dependencies=task_data.get("dependencies", [])
                )
                tasks.append(task)
            
            # Create Plan
            plan = Plan(
                query=query,
                tasks=tasks,
                status="created"
            )
            
            # Build dependency graph (for validation and execution order)
            from app.task_manager import TaskManager
            task_manager = TaskManager()
            for task in tasks:
                task_manager.add_task(task)
            
            # Validate dependency graph
            execution_order = task_manager.get_execution_order()
            self.logger.info(f"Created plan with {len(tasks)} tasks: {plan.plan_id}")
            self.logger.info(f"Execution order: {len(execution_order)} batches")
            
            # Sanitize response to remove control characters
            from app.utils.sanitize import safe_dict_to_json
            result_dict = plan.dict()
            # Add collection to plan_dict for use in plan_context
            if collection:
                result_dict["collection"] = collection
            return safe_dict_to_json(result_dict)
            
        except Exception as e:
            self.logger.error(f"Failed to create plan: {e}")
            raise
    
    def discover_tasks_from_result(
        self,
        completed_task_result: Dict[str, Any],
        original_query: str,
        existing_task_ids: List[str]
    ) -> List[Task]:
        """
        Discover new tasks based on completed task results.
        
        Phase 8: Dynamic task spawning
        
        Args:
            completed_task_result: Result from a completed task
            original_query: Original user query
            existing_task_ids: List of existing task IDs to avoid duplicates
            
        Returns:
            List of newly discovered tasks
        """
        self.logger.debug("Discovering tasks from result")
        
        # Check if result indicates need for additional tasks
        if not isinstance(completed_task_result, dict):
            return []
        
        # Check for explicit spawned_tasks in result
        if "spawned_tasks" in completed_task_result:
            spawned_data = completed_task_result["spawned_tasks"]
            if isinstance(spawned_data, list):
                new_tasks = []
                for task_data in spawned_data:
                    try:
                        params = TaskParameters(**task_data.get("parameters", {}))
                        task = Task(
                            task_id=task_data.get("task_id", f"task_{len(existing_task_ids) + len(new_tasks) + 1}"),
                            task_type=task_data.get("task_type", "RETRIEVE"),
                            description=task_data.get("description", ""),
                            parameters=params,
                            dependencies=task_data.get("dependencies", [])
                        )
                        new_tasks.append(task)
                    except Exception as e:
                        self.logger.error(f"Failed to create spawned task: {e}")
                return new_tasks
        
        # Analyze result to discover implicit tasks
        # For example, if RETRIEVE found many documents, might need additional ANALYZE tasks
        if "search_results" in completed_task_result:
            results = completed_task_result["search_results"]
            if isinstance(results, list) and len(results) > 10:
                # Many results found - might need additional analysis
                self.logger.debug(f"Found {len(results)} results, considering additional analysis task")
                # Could spawn an ANALYZE task here if needed
        
        return []
    
    async def execute_plan(self, plan: Dict[str, Any], executor) -> Dict[str, Any]:
        """
        Execute a task plan using the provided executor.
        
        Args:
            plan: Plan dictionary
            executor: TaskExecutor instance
        """
        from datetime import datetime
        from app.models.task_models import Plan, Task
        
        self.logger.debug(f"Executing plan: {plan.get('plan_id', 'unknown')}")
        
        plan_obj = None
        try:
            # Reconstruct Plan object from dict
            plan_obj = Plan(**plan)
            plan_obj.status = "executing"
            plan_obj.started_at = datetime.utcnow().isoformat()
            
            # Build plan context
            plan_context = {
                "query": plan_obj.query,
                "plan_id": plan_obj.plan_id,
                "collection": plan.get("collection"),  # Include collection in plan_context
                "task_results": {}
            }
            
            # Create TaskManager for execution
            from app.task_manager import TaskManager
            task_manager = TaskManager()
            for task in plan_obj.tasks:
                task_manager.add_task(task)
            
            # Execute all tasks (with dynamic spawning support)
            results = await executor.execute_tasks(plan_obj.tasks, plan_context, task_manager)
            
            # Update plan with any dynamically added tasks
            for task_id, task in task_manager.tasks.items():
                if task_id not in [t.task_id for t in plan_obj.tasks]:
                    plan_obj.tasks.append(task)
            
            # Get final result from GENERATE task (last task)
            final_result = None
            for task in plan_obj.tasks:
                if task.task_type == "GENERATE" and task.status == "completed":
                    final_result = task.result
                    break
            
            # If no GENERATE task, use last completed task result
            if not final_result:
                for task in reversed(plan_obj.tasks):
                    if task.status == "completed" and task.result:
                        final_result = task.result
                        break
            
            plan_obj.status = "completed"
            plan_obj.completed_at = datetime.utcnow().isoformat()
            plan_obj.final_result = final_result
            
            # Sanitize response to remove control characters
            from app.utils.sanitize import safe_dict_to_json
            result_dict = plan_obj.dict()
            return safe_dict_to_json(result_dict)
            
        except Exception as e:
            self.logger.error(f"Plan execution failed: {e}")
            if plan_obj is not None:
                plan_obj.status = "failed"
                plan_obj.completed_at = datetime.utcnow().isoformat()
            else:
                # If plan_obj wasn't created, return error response
                return {
                    "plan_id": plan.get("plan_id", "unknown"),
                    "status": "failed",
                    "error": str(e),
                    "query": plan.get("query", ""),
                    "tasks": []
                }
            raise

