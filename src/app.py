"""
Advanced Task Management API
A comprehensive REST API for managing tasks with priority, assignments, and analytics
"""
from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import hashlib
import json
import os
import time

# Enums for validation
class TaskStatus(str, Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    blocked = "blocked"
    cancelled = "cancelled"

class TaskPriority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"

class TaskCategory(str, Enum):
    development = "development"
    testing = "testing"
    documentation = "documentation"
    deployment = "deployment"
    bugfix = "bugfix"
    feature = "feature"

# Pydantic models
class TaskCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    priority: TaskPriority = TaskPriority.medium
    category: TaskCategory
    assignee: Optional[str] = Field(None, max_length=100)
    estimated_hours: Optional[float] = Field(None, ge=0, le=1000)
    tags: List[str] = Field(default_factory=list)
    dependencies: List[int] = Field(default_factory=list)
    
    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v):
        if len(v) > 10:
            raise ValueError('Maximum 10 tags allowed')
        return v

class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    category: Optional[TaskCategory] = None
    assignee: Optional[str] = Field(None, max_length=100)
    estimated_hours: Optional[float] = Field(None, ge=0, le=1000)
    actual_hours: Optional[float] = Field(None, ge=0, le=1000)
    tags: Optional[List[str]] = None
    dependencies: Optional[List[int]] = None

class Task(BaseModel):
    id: int
    title: str
    description: Optional[str]
    status: TaskStatus
    priority: TaskPriority
    category: TaskCategory
    assignee: Optional[str]
    estimated_hours: Optional[float]
    actual_hours: Optional[float]
    tags: List[str]
    dependencies: List[int]
    created_at: datetime
    updated_at: Optional[datetime]
    completed_at: Optional[datetime]
    checksum: str

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str
    uptime_seconds: float
    total_tasks: int
    memory_usage_mb: float

# Initialize FastAPI app
app = FastAPI(
    title="Task Management API",
    description="Advanced task management system with analytics",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage with complex structure
tasks: Dict[int, Dict] = {}
task_counter = 0
start_time = time.time()

# Simulated "heavy" operations cache
analytics_cache = {}
cache_expiry = {}

def calculate_checksum(task_data: dict) -> str:
    """Calculate SHA256 checksum of task data"""
    task_str = json.dumps(task_data, sort_keys=True, default=str)
    return hashlib.sha256(task_str.encode()).hexdigest()[:16]

def simulate_heavy_computation(data: dict, duration: float = 0.1):
    """Simulate CPU-intensive operation"""
    time.sleep(duration)
    # Perform some actual computation
    result = 0
    for i in range(10000):
        result += hash(f"{data}{i}") % 1000
    return result

async def background_analytics_update(task_id: int):
    """Background task for updating analytics"""
    await asyncio.sleep(1)
    # Simulate heavy analytics processing
    simulate_heavy_computation({"task_id": task_id}, 0.05)

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Comprehensive health check with system metrics"""
    uptime = time.time() - start_time
    
    # Simulate memory calculation
    memory_mb = len(json.dumps(tasks)) / 1024 / 1024
    
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        version="2.0.0",
        uptime_seconds=uptime,
        total_tasks=len(tasks),
        memory_usage_mb=round(memory_mb, 2)
    )

@app.get("/tasks", response_model=List[Task])
async def get_tasks(
    status: Optional[TaskStatus] = None,
    priority: Optional[TaskPriority] = None,
    category: Optional[TaskCategory] = None,
    assignee: Optional[str] = None,
    tags: Optional[str] = Query(None, description="Comma-separated tags"),
    sort_by: str = Query("created_at", pattern="^(created_at|priority|status|updated_at)$"),
    order: str = Query("desc", pattern="^(asc|desc)$"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """Get tasks with advanced filtering, sorting, and pagination"""
    
    # Filter tasks
    filtered_tasks = list(tasks.values())
    
    if status:
        filtered_tasks = [t for t in filtered_tasks if t['status'] == status]
    if priority:
        filtered_tasks = [t for t in filtered_tasks if t['priority'] == priority]
    if category:
        filtered_tasks = [t for t in filtered_tasks if t['category'] == category]
    if assignee:
        filtered_tasks = [t for t in filtered_tasks if t['assignee'] == assignee]
    if tags:
        tag_list = [t.strip() for t in tags.split(',')]
        filtered_tasks = [t for t in filtered_tasks if any(tag in t['tags'] for tag in tag_list)]
    
    # Simulate heavy filtering computation
    if len(filtered_tasks) > 50:
        simulate_heavy_computation({"filter": "heavy"}, 0.05)
    
    # Sort tasks
    priority_order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
    reverse = order == "desc"
    
    if sort_by == "priority":
        filtered_tasks.sort(key=lambda x: priority_order.get(x['priority'], 0), reverse=reverse)
    else:
        filtered_tasks.sort(key=lambda x: x.get(sort_by, ""), reverse=reverse)
    
    # Pagination
    paginated_tasks = filtered_tasks[offset:offset + limit]
    
    return paginated_tasks

@app.get("/tasks/{task_id}", response_model=Task)
async def get_task(task_id: int):
    """Get a specific task by ID with dependency resolution"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = tasks[task_id]
    
    # Simulate dependency resolution computation
    if task['dependencies']:
        simulate_heavy_computation({"dependencies": task['dependencies']}, 0.02)
    
    return task

@app.post("/tasks", response_model=Task, status_code=201)
async def create_task(task_data: TaskCreate, background_tasks: BackgroundTasks):
    """Create a new task with validation"""
    global task_counter
    
    # Validate dependencies exist
    for dep_id in task_data.dependencies:
        if dep_id not in tasks:
            raise HTTPException(status_code=400, detail=f"Dependency task {dep_id} not found")
    
    task_counter += 1
    now = datetime.utcnow()
    
    task_dict = {
        'id': task_counter,
        'title': task_data.title,
        'description': task_data.description,
        'status': TaskStatus.pending,
        'priority': task_data.priority,
        'category': task_data.category,
        'assignee': task_data.assignee,
        'estimated_hours': task_data.estimated_hours,
        'actual_hours': None,
        'tags': task_data.tags,
        'dependencies': task_data.dependencies,
        'created_at': now,
        'updated_at': None,
        'completed_at': None,
        'checksum': ''
    }
    
    task_dict['checksum'] = calculate_checksum(task_dict)
    tasks[task_counter] = task_dict
    
    # Trigger background analytics update
    background_tasks.add_task(background_analytics_update, task_counter)
    
    return task_dict

@app.put("/tasks/{task_id}", response_model=Task)
async def update_task(task_id: int, task_update: TaskUpdate, background_tasks: BackgroundTasks):
    """Update an existing task"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = tasks[task_id]
    update_data = task_update.model_dump(exclude_unset=True)
    
    # Validate dependencies if provided
    if 'dependencies' in update_data:
        for dep_id in update_data['dependencies']:
            if dep_id not in tasks and dep_id != task_id:
                raise HTTPException(status_code=400, detail=f"Dependency task {dep_id} not found")
    
    # Update fields
    for field, value in update_data.items():
        task[field] = value
    
    task['updated_at'] = datetime.utcnow()
    
    # Mark completion timestamp
    if task_update.status == TaskStatus.completed and not task.get('completed_at'):
        task['completed_at'] = datetime.utcnow()
    
    # Recalculate checksum
    task['checksum'] = calculate_checksum(task)
    
    # Simulate heavy update computation
    simulate_heavy_computation({"update": task_id}, 0.03)
    
    # Trigger background analytics update
    background_tasks.add_task(background_analytics_update, task_id)
    
    return task

@app.delete("/tasks/{task_id}")
async def delete_task(task_id: int):
    """Delete a task and update dependent tasks"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Check for dependent tasks
    dependent_tasks = [t for t in tasks.values() if task_id in t['dependencies']]
    
    if dependent_tasks:
        # Remove this task from dependencies
        for dep_task in dependent_tasks:
            dep_task['dependencies'].remove(task_id)
            dep_task['updated_at'] = datetime.utcnow()
    
    del tasks[task_id]
    
    # Clear analytics cache
    analytics_cache.clear()
    
    return {"message": "Task deleted successfully", "affected_tasks": len(dependent_tasks)}

@app.get("/tasks/stats/summary")
async def get_task_statistics():
    """Get comprehensive task statistics with heavy computation"""
    
    # Check cache
    cache_key = "stats_summary"
    if cache_key in analytics_cache and cache_key in cache_expiry:
        if datetime.utcnow() < cache_expiry[cache_key]:
            return analytics_cache[cache_key]
    
    # Simulate heavy analytics computation
    simulate_heavy_computation({"stats": "all"}, 0.1)
    
    stats = {
        'total': len(tasks),
        'by_status': {},
        'by_priority': {},
        'by_category': {},
        'by_assignee': {},
        'completion_rate': 0.0,
        'average_estimated_hours': 0.0,
        'average_actual_hours': 0.0,
        'overdue_tasks': 0,
        'blocked_tasks': 0
    }
    
    # Calculate statistics
    for task in tasks.values():
        # By status
        status = task['status']
        stats['by_status'][status] = stats['by_status'].get(status, 0) + 1
        
        # By priority
        priority = task['priority']
        stats['by_priority'][priority] = stats['by_priority'].get(priority, 0) + 1
        
        # By category
        category = task['category']
        stats['by_category'][category] = stats['by_category'].get(category, 0) + 1
        
        # By assignee
        assignee = task['assignee'] or 'unassigned'
        stats['by_assignee'][assignee] = stats['by_assignee'].get(assignee, 0) + 1
    
    # Calculate completion rate
    completed = stats['by_status'].get('completed', 0)
    if stats['total'] > 0:
        stats['completion_rate'] = round(completed / stats['total'] * 100, 2)
    
    # Calculate average hours
    estimated_hours = [t['estimated_hours'] for t in tasks.values() if t['estimated_hours']]
    actual_hours = [t['actual_hours'] for t in tasks.values() if t['actual_hours']]
    
    if estimated_hours:
        stats['average_estimated_hours'] = round(sum(estimated_hours) / len(estimated_hours), 2)
    if actual_hours:
        stats['average_actual_hours'] = round(sum(actual_hours) / len(actual_hours), 2)
    
    stats['blocked_tasks'] = stats['by_status'].get('blocked', 0)
    
    # Cache results for 60 seconds
    analytics_cache[cache_key] = stats
    cache_expiry[cache_key] = datetime.utcnow() + timedelta(seconds=60)
    
    return stats

@app.get("/tasks/analytics/productivity")
async def get_productivity_analytics():
    """Complex productivity analytics with heavy computation"""
    
    # Simulate very heavy computation
    simulate_heavy_computation({"analytics": "productivity"}, 0.15)
    
    analytics = {
        'total_estimated_hours': 0,
        'total_actual_hours': 0,
        'efficiency_rate': 0.0,
        'tasks_by_assignee': {},
        'completion_trend': [],
        'priority_distribution': {},
        'category_performance': {}
    }
    
    # Calculate productivity metrics
    for task in tasks.values():
        assignee = task['assignee'] or 'unassigned'
        
        if assignee not in analytics['tasks_by_assignee']:
            analytics['tasks_by_assignee'][assignee] = {
                'total': 0,
                'completed': 0,
                'in_progress': 0,
                'estimated_hours': 0,
                'actual_hours': 0
            }
        
        analytics['tasks_by_assignee'][assignee]['total'] += 1
        
        if task['status'] == 'completed':
            analytics['tasks_by_assignee'][assignee]['completed'] += 1
        elif task['status'] == 'in_progress':
            analytics['tasks_by_assignee'][assignee]['in_progress'] += 1
        
        if task['estimated_hours']:
            analytics['tasks_by_assignee'][assignee]['estimated_hours'] += task['estimated_hours']
            analytics['total_estimated_hours'] += task['estimated_hours']
        
        if task['actual_hours']:
            analytics['tasks_by_assignee'][assignee]['actual_hours'] += task['actual_hours']
            analytics['total_actual_hours'] += task['actual_hours']
    
    # Calculate efficiency rate
    if analytics['total_estimated_hours'] > 0 and analytics['total_actual_hours'] > 0:
        analytics['efficiency_rate'] = round(
            analytics['total_estimated_hours'] / analytics['total_actual_hours'] * 100, 2
        )
    
    return analytics

@app.post("/tasks/bulk")
async def bulk_create_tasks(tasks_data: List[TaskCreate], background_tasks: BackgroundTasks):
    """Bulk create multiple tasks"""
    if len(tasks_data) > 100:
        raise HTTPException(status_code=400, detail="Maximum 100 tasks per bulk operation")
    
    created_tasks = []
    
    for task_data in tasks_data:
        task = await create_task(task_data, background_tasks)
        created_tasks.append(task)
    
    # Simulate heavy bulk operation
    simulate_heavy_computation({"bulk": len(tasks_data)}, 0.1)
    
    return {
        "message": f"Successfully created {len(created_tasks)} tasks",
        "task_ids": [t['id'] for t in created_tasks]
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)