"""
Task state management and dependency graph management
"""

import logging
from typing import Dict, Any, List, Set, Optional
from collections import defaultdict, deque
from app.models.task_models import Task, TaskStatus

logger = logging.getLogger(__name__)

class TaskManager:
    """Manages task state and dependency graph"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.tasks: Dict[str, Task] = {}
        self.dependency_graph: Dict[str, Set[str]] = defaultdict(set)  # task_id -> set of dependent task_ids
        self.reverse_dependency_graph: Dict[str, Set[str]] = defaultdict(set)  # task_id -> set of tasks it depends on
        self.logger.info("Task Manager initialized")
    
    def add_task(self, task: Task):
        """Add a task to the manager"""
        self.tasks[task.task_id] = task
        
        # Build dependency graphs
        for dep_id in task.dependencies:
            self.dependency_graph[dep_id].add(task.task_id)
            self.reverse_dependency_graph[task.task_id].add(dep_id)
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID"""
        return self.tasks.get(task_id)
    
    def get_ready_tasks(self, completed_tasks: Set[str]) -> List[Task]:
        """
        Get tasks that are ready to execute (all dependencies completed)
        
        Args:
            completed_tasks: Set of task IDs that have been completed
            
        Returns:
            List of tasks ready to execute
        """
        ready_tasks = []
        
        for task_id, task in self.tasks.items():
            # Skip if already completed or failed
            if task.status in ["completed", "failed"]:
                continue
            
            # Skip if already running or in_progress
            if task.status in ["running", "in_progress"]:
                continue
            
            # Check if all dependencies are completed
            if task.dependencies:
                all_deps_complete = all(dep_id in completed_tasks for dep_id in task.dependencies)
                if not all_deps_complete:
                    continue
            
            ready_tasks.append(task)
        
        return ready_tasks
    
    def get_dependent_tasks(self, task_id: str) -> List[Task]:
        """Get all tasks that depend on the given task"""
        dependent_ids = self.dependency_graph.get(task_id, set())
        return [self.tasks[tid] for tid in dependent_ids if tid in self.tasks]
    
    def update_task_status(self, task_id: str, status: TaskStatus, result: Optional[Dict[str, Any]] = None, error: Optional[str] = None):
        """Update task status"""
        if task_id not in self.tasks:
            self.logger.warning(f"Task {task_id} not found in manager")
            return
        
        task = self.tasks[task_id]
        task.status = status
        
        if result is not None:
            task.result = result
        
        if error is not None:
            task.error = error
    
    def get_execution_order(self) -> List[List[Task]]:
        """
        Get tasks in execution order (topological sort)
        Returns list of task batches that can be executed in parallel
        """
        # Build in-degree map
        in_degree = {task_id: len(self.reverse_dependency_graph.get(task_id, set())) 
                    for task_id in self.tasks.keys()}
        
        # Find tasks with no dependencies (can start immediately)
        queue = deque([task_id for task_id, degree in in_degree.items() if degree == 0])
        execution_order = []
        processed = set()
        
        while queue:
            # Current batch of tasks that can run in parallel
            current_batch = []
            batch_size = len(queue)
            
            for _ in range(batch_size):
                task_id = queue.popleft()
                if task_id in processed:
                    continue
                
                task = self.tasks[task_id]
                current_batch.append(task)
                processed.add(task_id)
                
                # Update dependent tasks
                for dependent_id in self.dependency_graph.get(task_id, set()):
                    in_degree[dependent_id] -= 1
                    if in_degree[dependent_id] == 0:
                        queue.append(dependent_id)
            
            if current_batch:
                execution_order.append(current_batch)
        
        # Add any remaining tasks (shouldn't happen in valid DAG, but handle gracefully)
        remaining = [task for task_id, task in self.tasks.items() if task_id not in processed]
        if remaining:
            self.logger.warning(f"Found {len(remaining)} tasks with circular dependencies or missing dependencies")
            execution_order.append(remaining)
        
        return execution_order
    
    def get_task_status_summary(self) -> Dict[str, Any]:
        """Get summary of all task statuses"""
        summary = {
            "total": len(self.tasks),
            "pending": 0,
            "running": 0,
            "completed": 0,
            "failed": 0
        }
        
        for task in self.tasks.values():
            summary[task.status] = summary.get(task.status, 0) + 1
        
        return summary
    
    def add_dynamic_tasks(self, new_tasks: List[Task], parent_task_id: Optional[str] = None):
        """
        Add dynamically spawned tasks to the dependency graph.
        
        Phase 8: Dynamic task spawning
        
        Args:
            new_tasks: List of new tasks to add
            parent_task_id: Optional parent task ID (new tasks will depend on this)
        """
        self.logger.info(f"Adding {len(new_tasks)} dynamic tasks (parent: {parent_task_id})")
        
        for task in new_tasks:
            # Add parent dependency if specified
            if parent_task_id and parent_task_id not in task.dependencies:
                task.dependencies.append(parent_task_id)
            
            # Add task to manager
            self.add_task(task)
            
            self.logger.debug(f"Added dynamic task: {task.task_id} (dependencies: {task.dependencies})")
    
    def update_dependency_graph(self):
        """Rebuild dependency graphs after adding new tasks"""
        # Clear existing graphs
        self.dependency_graph.clear()
        self.reverse_dependency_graph.clear()
        
        # Rebuild graphs
        for task in self.tasks.values():
            for dep_id in task.dependencies:
                self.dependency_graph[dep_id].add(task.task_id)
                self.reverse_dependency_graph[task.task_id].add(dep_id)

