"""
Pydantic models for task planning
"""

from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel
from datetime import datetime
import uuid

TaskType = Literal["RETRIEVE", "ANALYZE", "GENERATE"]
TaskStatus = Literal["pending", "pending", "in_progress", "running", "completed", "failed"]

class TaskDependency(BaseModel):
    """Task dependency relationship"""
    task_id: str
    required_status: TaskStatus = "completed"

class TaskParameters(BaseModel):
    """Task parameters - flexible structure for different task types"""
    # For RETRIEVE tasks
    search_query: Optional[str] = None
    collection: Optional[str] = None
    limit: Optional[int] = 5
    
    # For ANALYZE tasks
    analysis_type: Optional[str] = None
    input_tasks: Optional[List[str]] = None
    input_task: Optional[str] = None
    
    # For GENERATE tasks
    response_type: Optional[str] = None
    response_format: Optional[str] = None
    
    # Additional flexible parameters
    extra: Optional[Dict[str, Any]] = None

class Task(BaseModel):
    """Individual task in a plan"""
    task_id: str
    task_type: TaskType
    description: str
    parameters: TaskParameters
    dependencies: List[str] = []  # List of task_ids this task depends on
    status: TaskStatus = "pending"
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: str = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    
    def __init__(self, **data):
        if 'created_at' not in data or data.get('created_at') is None:
            data['created_at'] = datetime.utcnow().isoformat()
        super().__init__(**data)

class Plan(BaseModel):
    """Complete task plan"""
    plan_id: str
    query: str
    tasks: List[Task]
    status: str = "created"  # created, executing, completed, failed
    created_at: str = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    final_result: Optional[Dict[str, Any]] = None
    
    def __init__(self, **data):
        if 'plan_id' not in data or not data.get('plan_id'):
            data['plan_id'] = str(uuid.uuid4())
        if 'created_at' not in data or data.get('created_at') is None:
            data['created_at'] = datetime.utcnow().isoformat()
        super().__init__(**data)

