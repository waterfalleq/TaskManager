from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.auth.jwt_handler import get_current_user
from app.db.database import get_db
from app.models.enums import TaskPriority, TaskStatus
from app.models.models import User
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse
from app.crud.task_crud import (
    create_task,
    get_tasks_by_user,
    get_task_by_id,
    update_task,
    delete_task,
    search_tasks,
)

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/", response_model=TaskResponse)
def create_task_handler(
    task: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new task for the current user."""
    return create_task(db, task, owner_id=current_user.id)


@router.get("/", response_model=List[TaskResponse])
def get_tasks_by_user_handler(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    status: Optional[TaskStatus] = Query(None, description="Filter by task status"),
    priority: Optional[TaskPriority] = Query(
        None, description="Filter by task priority"
    ),
    deadline_before: Optional[datetime] = Query(
        None, description="Tasks with deadline before this date"
    ),
    deadline_after: Optional[datetime] = Query(
        None, description="Tasks with deadline after this date"
    ),
    limit: int = Query(100, description="Maximum number of tasks to return"),
    offset: int = Query(0, description="Number of tasks to skip"),
    order_by: str = Query(
        "created_at", description="Sort by 'created_at' or 'deadline'"
    ),
    order_dir: str = Query("asc", description="Sort direction: 'asc' or 'desc'"),
    show_completed: bool = Query(
        True, description="Whether to include completed tasks"
    ),
):
    """Retrieve all tasks belonging to the current user with filters and sorting."""
    tasks = get_tasks_by_user(
        db=db,
        user_id=current_user.id,
        status=status,
        priority=priority,
        deadline_before=deadline_before,
        deadline_after=deadline_after,
        limit=limit,
        offset=offset,
        order_by=order_by,
        order_dir=order_dir,
        show_completed=show_completed,
    )
    return tasks


@router.get("/search", response_model=List[TaskResponse])
def search_tasks_handler(
    title: str = None,
    description: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Search for tasks owned by the current user."""
    tasks = search_tasks(
        db=db, owner_id=current_user.id, title=title, description=description
    )
    return tasks


@router.get("/{task_id}", response_model=TaskResponse)
def get_task_by_id_handler(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Fetch a specific task if owned by the current user."""
    task = get_task_by_id(db, task_id)
    if task.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed to access this task")
    return task


@router.put("/{task_id}", response_model=TaskResponse)
def update_task_handler(
    task: TaskUpdate,
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a task if owned by the current user."""
    existing_task = get_task_by_id(db, task_id)
    if existing_task.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed to update this task")

    return update_task(db, task_id, task)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task_handler(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a task if owned by the current user."""
    task = get_task_by_id(db, task_id)
    if task.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed to delete this task")

    delete_task(db, task_id)
