"""
Task execution logic
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List, Set
from app.models.task_models import Task, TaskType
from app.tasks.retrieve_task import RetrieveTask
from app.tasks.analyze_task import AnalyzeTask
from app.tasks.generate_task import GenerateTask
from app.task_manager import TaskManager

logger = logging.getLogger(__name__)

class TaskExecutor:
    """Handles task execution"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.info("Task Executor initialized")
    
    def _create_task_instance(self, task: Task):
        """Create appropriate task instance based on task type"""
        if task.task_type == "RETRIEVE":
            return RetrieveTask(task)
        elif task.task_type == "ANALYZE":
            return AnalyzeTask(task)
        elif task.task_type == "GENERATE":
            return GenerateTask(task)
        else:
            raise ValueError(f"Unknown task type: {task.task_type}")
    
    async def execute_task(self, task: Task, plan_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a single task.
        
        Args:
            task: Task object to execute
            plan_context: Context from the plan (query, user_id, session_id, task_results, etc.)
        """
        self.logger.debug(f"Executing task: {task.task_id} ({task.task_type})")
        
        try:
            # Create task instance
            task_instance = self._create_task_instance(task)
            
            # Execute task
            result = await task_instance.execute(plan_context)
            
            # Store result in plan context
            if 'task_results' not in plan_context:
                plan_context['task_results'] = {}
            plan_context['task_results'][task.task_id] = result
            
            return result
            
        except Exception as e:
            self.logger.error(f"Task execution failed: {e}")
            task.status = "failed"
            task.error = str(e)
            raise
    
    async def execute_tasks(self, tasks: List[Task], plan_context: Dict[str, Any], task_manager: Optional[TaskManager] = None) -> List[Dict[str, Any]]:
        """
        Execute multiple tasks with parallel execution for independent tasks.
        
        Phase 6: Parallel execution with dependency resolution
        Phase 8: Dynamic task spawning during execution
        
        Args:
            tasks: List of Task objects
            plan_context: Context from the plan
            task_manager: Optional TaskManager (if None, creates new one)
        """
        self.logger.debug(f"Executing {len(tasks)} tasks with parallel execution")
        
        # Create or use provided TaskManager
        if task_manager is None:
            task_manager = TaskManager()
            for task in tasks:
                task_manager.add_task(task)
        else:
            # Add any new tasks to existing manager
            for task in tasks:
                if task.task_id not in task_manager.tasks:
                    task_manager.add_task(task)
        
        # Store task_manager in plan_context for dynamic spawning
        plan_context['task_manager'] = task_manager
        
        completed_tasks: Set[str] = set()
        results = []
        max_iterations = 20  # Prevent infinite loops
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            self.logger.debug(f"Execution iteration {iteration}")
            
            # Get ready tasks (all dependencies completed)
            ready_tasks = task_manager.get_ready_tasks(completed_tasks)
            
            if not ready_tasks:
                # Check if all tasks are done
                all_done = all(
                    task.status in ["completed", "failed"] 
                    for task in task_manager.tasks.values()
                )
                if all_done:
                    break
                
                # Wait a bit and check again (for dynamic tasks that might be added)
                await asyncio.sleep(0.1)
                continue
            
            self.logger.info(f"Iteration {iteration}: Executing {len(ready_tasks)} ready tasks")
            
            # Execute ready tasks in parallel
            batch_results = await asyncio.gather(
                *[self._execute_task_with_error_handling(task, plan_context) for task in ready_tasks],
                return_exceptions=True
            )
            
            # Process results and check for dynamic task spawning
            new_tasks_spawned = False
            for i, result in enumerate(batch_results):
                task = ready_tasks[i]
                
                if isinstance(result, Exception):
                    self.logger.error(f"Task {task.task_id} failed with exception: {result}")
                    error_msg = str(result)
                    if task_manager:
                        task_manager.update_task_status(task.task_id, "failed", error=error_msg)
                    # Also update task object directly
                    task.status = "failed"
                    task.error = error_msg
                    results.append({
                        "task_id": task.task_id,
                        "status": "failed",
                        "error": error_msg
                    })
                else:
                    completed_tasks.add(task.task_id)
                    results.append(result)
                    self.logger.info(f"Task {task.task_id} completed successfully")
                    
                    # Task status already updated in _execute_task_with_error_handling
                    # Just ensure it's synced
                    if task_manager:
                        # Double-check status is updated (should already be done)
                        current_task = task_manager.get_task(task.task_id)
                        if current_task and current_task.status != task.status:
                            task_manager.update_task_status(
                                task.task_id,
                                task.status,
                                result=task.result,
                                error=task.error
                            )
                    
                    # Check if task spawned new tasks
                    if isinstance(result, dict) and result.get("spawned_tasks"):
                        spawned = result["spawned_tasks"]
                        if spawned:
                            new_tasks_spawned = True
                            self.logger.info(f"Task {task.task_id} spawned {len(spawned)} new tasks")
            
            # If new tasks were spawned, continue loop to execute them
            if not new_tasks_spawned:
                # Check if there are any pending tasks
                pending = [
                    t for t in task_manager.tasks.values() 
                    if t.status == "pending" and t.task_id not in completed_tasks
                ]
                if not pending:
                    break
        
        if iteration >= max_iterations:
            self.logger.warning(f"Reached max iterations ({max_iterations}), stopping execution")
        
        return results
    
    async def _execute_task_with_error_handling(self, task: Task, plan_context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single task with error handling and dynamic task discovery"""
        task_manager = plan_context.get('task_manager')
        
        try:
            # Update task_manager immediately for streaming (before task instance is created)
            # The task instance will call mark_started() internally, but we update manager here
            # so polling can catch the status change
            if task_manager:
                task_manager.update_task_status(task.task_id, "in_progress")
                # Also update the task object directly
                task.status = "in_progress"
                from datetime import datetime
                task.started_at = datetime.utcnow().isoformat()
            
            # Small delay to allow polling to catch status update
            await asyncio.sleep(0.2)
            
            result = await self.execute_task(task, plan_context)
            
            # Update task_manager when task completes (already done above, but ensure sync)
            if task_manager:
                task_manager.update_task_status(
                    task.task_id,
                    task.status,
                    result=task.result,
                    error=task.error
                )
            
            # Phase 8: Check for dynamic task spawning
            planner = plan_context.get('planner')  # Use planner from context instead of creating new
            if task_manager and planner and isinstance(result, dict):
                # Check if task result indicates need for additional tasks
                existing_task_ids = list(task_manager.tasks.keys())
                discovered_tasks = planner.discover_tasks_from_result(
                    completed_task_result=result,
                    original_query=plan_context.get("query", ""),
                    existing_task_ids=existing_task_ids
                )
                
                if discovered_tasks:
                    # Add discovered tasks to manager
                    task_manager.add_dynamic_tasks(discovered_tasks, parent_task_id=task.task_id)
                    
                    # Update result to indicate spawned tasks
                    if "spawned_tasks" not in result:
                        result["spawned_tasks"] = [t.dict() for t in discovered_tasks]
            
            return result
        except Exception as e:
            self.logger.error(f"Task {task.task_id} execution failed: {e}")
            task.status = "failed"
            task.error = str(e)
            raise

