import os
from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID, uuid4

import redis
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
from pydantic import BaseModel, Field

app = FastAPI()

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv('ALLOWED_ORIGINS', '').split(','),
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# Rate limiting setup
redis_client = redis.Redis(host=os.getenv('REDIS_HOST', 'localhost'), port=int(os.getenv('REDIS_PORT', 6379)), db=0)
FastAPILimiter.init(redis_client)

# OAuth2 setup
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')

class Priority(str, Enum):
    low = 'low'
    medium = 'medium'
    high = 'high'

class Status(str, Enum):
    todo = 'todo'
    in_progress = 'in_progress'
    done = 'done'

class Task(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    title: str
    description: Optional[str] = None
    due_date: datetime
    priority: Priority
    status: Status

# In-memory storage for tasks
tasks = {}

@app.post('/tasks/', response_model=Task, dependencies=[Depends(RateLimiter(times=10, seconds=60))])
def create_task(task: Task):
    if task.id in tasks:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Task with this ID already exists')
    tasks[task.id] = task
    return task

@app.get('/tasks/', response_model=List[Task], dependencies=[Depends(RateLimiter(times=10, seconds=60))])
def read_tasks(skip: int = 0, limit: int = 10):
    return list(tasks.values())[skip:skip + limit]

@app.get('/tasks/{task_id}', response_model=Task, dependencies=[Depends(RateLimiter(times=10, seconds=60))])
def read_task(task_id: UUID):
    try:
        task_id = UUID(task_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Invalid task ID format')
    if task_id not in tasks:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Task not found')
    return tasks[task_id]

@app.put('/tasks/{task_id}', response_model=Task, dependencies=[Depends(RateLimiter(times=10, seconds=60))])
def update_task(task_id: UUID, updated_task: Task):
    if task_id not in tasks:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Task not found')
    if updated_task.id != task_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Cannot update task ID')
    tasks[task_id] = updated_task
    return updated_task

@app.delete('/tasks/{task_id}', response_model=Task, dependencies=[Depends(RateLimiter(times=10, seconds=60))])
def delete_task(task_id: UUID):
    if task_id not in tasks:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Task not found')
    deleted_task = tasks.pop(task_id)
    return deleted_task

@app.get('/tasks/filter/', response_model=List[Task], dependencies=[Depends(RateLimiter(times=10, seconds=60))])
def filter_tasks(priority: Optional[Priority] = None, status: Optional[Status] = None):
    filtered_tasks = list(tasks.values())
    if priority:
        filtered_tasks = [task for task in filtered_tasks if task.priority == priority]
    if status:
        filtered_tasks = [task for task in filtered_tasks if task.status == status]
    return filtered_tasks

@app.get('/tasks/sort/', response_model=List[Task], dependencies=[Depends(RateLimiter(times=10, seconds=60))])
def sort_tasks(sort_by: str):
    if sort_by not in ['due_date', 'priority', 'status']:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Invalid sort criteria. Valid options are: due_date, priority, status')
    if sort_by == 'due_date':
        return sorted(tasks.values(), key=lambda task: task.due_date)
    elif sort_by == 'priority':
        return sorted(tasks.values(), key=lambda task: task.priority)
    elif sort_by == 'status':
        return sorted(tasks.values(), key=lambda task: task.status)
