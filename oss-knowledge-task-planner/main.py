"""
OSS Knowledge Task Planner Service
Handles complex task planning, decomposition, and execution with dependencies.
"""

import logging
import os
import json
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.planner import TaskPlanner
from app.executor import TaskExecutor
from app.task_manager import TaskManager
from app.models.task_models import Plan, Task

# Setup logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Request/Response models
class PlanRequest(BaseModel):
    query: str
    user_id: Optional[int] = None
    session_id: Optional[str] = None
    chat_context: Optional[dict] = None
    collection: Optional[str] = None

task_planner_service: Optional[TaskPlanner] = None
task_executor_service: Optional[TaskExecutor] = None
active_plans: Dict[str, Dict[str, Any]] = {}  # plan_id -> plan data with task_manager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    global task_planner_service, task_executor_service
    # Startup
    logger.info("Starting OSS Knowledge Task Planner Service")
    task_planner_service = TaskPlanner()
    task_executor_service = TaskExecutor()
    logger.info("Task Planner service ready - Port 8004")
    yield
    # Shutdown
    logger.info("Shutting down Task Planner service")

app = FastAPI(
    title="OSS Knowledge Task Planner Service",
    description="Handles complex task planning, decomposition, and execution with dependencies.",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "task-planner",
        "version": "1.0.0",
        "port": 8004
    }

@app.get("/")
async def root():
    """Root endpoint with basic service information"""
    return {
        "message": "OSS Knowledge Task Planner Service",
        "version": "1.0.0",
        "status": "running"
    }

@app.post("/plan")
async def create_plan(request: PlanRequest):
    """Create a task plan from a query"""
    if task_planner_service is None:
        raise HTTPException(status_code=503, detail="Task Planner service not initialized")
    
    try:
        plan_dict = await task_planner_service.create_plan(
            query=request.query,
            user_id=request.user_id,
            session_id=request.session_id,
            chat_context=request.chat_context,
            collection=request.collection
        )
        
        # Create TaskManager for this plan
        plan_obj = Plan(**plan_dict)
        task_manager = TaskManager()
        for task_dict in plan_dict.get("tasks", []):
            task = Task(**task_dict)
            task_manager.add_task(task)
        
        # Store plan with task manager
        active_plans[plan_dict["plan_id"]] = {
            "plan": plan_dict,
            "task_manager": task_manager
        }
        
        # Sanitize response to ensure valid JSON
        from app.utils.sanitize import safe_dict_to_json
        sanitized_plan = safe_dict_to_json(plan_dict)
        
        return sanitized_plan
    except Exception as e:
        logger.error(f"Error creating plan: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/execute")
async def execute_plan(request: dict):
    """Execute a task plan"""
    if task_planner_service is None or task_executor_service is None:
        raise HTTPException(status_code=503, detail="Task Planner service not initialized")
    
    try:
        plan_id = request.get("plan_id")
        task_manager = None
        if plan_id and plan_id in active_plans:
            # Use stored plan
            plan_dict = active_plans[plan_id]["plan"]
            task_manager = active_plans[plan_id]["task_manager"]
        else:
            # Use provided plan
            plan_dict = request
        
        result = await task_planner_service.execute_plan(plan_dict, task_executor_service)
        
        # Update stored plan and sync task manager
        if plan_id and plan_id in active_plans:
            active_plans[plan_id]["plan"] = result
            # Update task manager with latest task statuses from result
            task_manager = active_plans[plan_id]["task_manager"]
            if "tasks" in result:
                for task_dict in result["tasks"]:
                    task_id = task_dict.get("task_id")
                    if task_id and task_manager.get_task(task_id):
                        task_manager.update_task_status(
                            task_id,
                            task_dict.get("status", "pending"),
                            result=task_dict.get("result"),
                            error=task_dict.get("error")
                        )
        
        # Sanitize response to ensure valid JSON
        from app.utils.sanitize import safe_dict_to_json
        sanitized_result = safe_dict_to_json(result)
        
        # Return as JSONResponse to ensure proper encoding
        return JSONResponse(content=sanitized_result)
    except Exception as e:
        logger.error(f"Error executing plan: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """Get status of a specific task"""
    # Search through all active plans
    for plan_id, plan_data in active_plans.items():
        task_manager = plan_data["task_manager"]
        task = task_manager.get_task(task_id)
        if task:
            # Sanitize result to remove control characters
            from app.utils.sanitize import sanitize_json_string
            result = {
                "task_id": task.task_id,
                "task_type": task.task_type,
                "description": task.description,
                "status": task.status,
                "dependencies": task.dependencies,
                "result": sanitize_json_string(task.result) if task.result else None,
                "error": task.error,
                "created_at": task.created_at,
                "started_at": task.started_at,
                "completed_at": task.completed_at
            }
            return result
    
    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

@app.get("/plans/{plan_id}/status")
async def get_plan_status(plan_id: str):
    """Get status of a plan and all its tasks"""
    if plan_id not in active_plans:
        raise HTTPException(status_code=404, detail=f"Plan {plan_id} not found")
    
    plan_data = active_plans[plan_id]
    plan_dict = plan_data["plan"]
    task_manager = plan_data["task_manager"]
    
    # Get task status summary
    task_summary = task_manager.get_task_status_summary()
    
    # Get all tasks
    tasks = []
    for task_id, task in task_manager.tasks.items():
        tasks.append({
            "task_id": task.task_id,
            "task_type": task.task_type,
            "description": task.description,
            "status": task.status,
            "dependencies": task.dependencies,
            "error": task.error
        })
    
    return {
        "plan_id": plan_id,
        "query": plan_dict.get("query"),
        "status": plan_dict.get("status"),
        "task_summary": task_summary,
        "tasks": tasks,
        "created_at": plan_dict.get("created_at"),
        "started_at": plan_dict.get("started_at"),
        "completed_at": plan_dict.get("completed_at")
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8004,
        reload=True
    )

