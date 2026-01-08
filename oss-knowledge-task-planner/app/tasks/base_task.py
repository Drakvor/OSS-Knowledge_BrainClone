"""
Base task class for all task types
"""

import logging
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
from app.models.task_models import Task, TaskStatus

logger = logging.getLogger(__name__)

class BaseTask(ABC):
    """Base class for all task types"""
    
    def __init__(self, task: Task):
        self.task = task
        self.logger = logging.getLogger(__name__)
    
    @abstractmethod
    async def execute(self, plan_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the task
        
        Args:
            plan_context: Context from the plan (query, user_id, session_id, etc.)
            
        Returns:
            Dict with task execution result
        """
        pass
    
    def get_dependency_results(self, plan_context: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Get results from dependency tasks"""
        dependency_results = {}
        for dep_task_id in self.task.dependencies:
            if 'task_results' in plan_context:
                if dep_task_id in plan_context['task_results']:
                    dependency_results[dep_task_id] = plan_context['task_results'][dep_task_id]
        return dependency_results
    
    def mark_started(self):
        """Mark task as started"""
        from datetime import datetime
        # Use "in_progress" status to match what orchestrator expects
        self.task.status = "in_progress"
        self.task.started_at = datetime.utcnow().isoformat()
    
    def mark_completed(self, result: Dict[str, Any]):
        """Mark task as completed with result"""
        from datetime import datetime
        self.task.status = "completed"
        self.task.result = result
        self.task.completed_at = datetime.utcnow().isoformat()
    
    def mark_failed(self, error: str):
        """Mark task as failed with error"""
        from datetime import datetime
        self.task.status = "failed"
        self.task.error = error
        self.task.completed_at = datetime.utcnow().isoformat()

