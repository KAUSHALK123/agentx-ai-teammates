from typing import List
from fastapi import APIRouter, HTTPException, status
from app.models.task import Task
from app.schemas.task import (
    TaskCreateRequest,
    TaskResponse,
    TaskDetailResponse,
)
from app.services.orchestrator import get_orchestrator
from app.services.task_store import get_task_store

router = APIRouter()


@router.post(
    "",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create and execute a business task",
)
async def create_task(request: TaskCreateRequest) -> TaskResponse:
    """Accept a business request, select an agent teammate, plan, execute, and verify."""
    orchestrator = get_orchestrator()
    task: Task = await orchestrator.create_and_run_task(
        user_request=request.user_request,
        explicit_agent=request.selected_agent,
    )
    return TaskResponse(
        task_id=task.task_id,
        selected_agent=task.selected_agent,
        status=task.status,
    )


@router.get(
    "/{task_id}",
    response_model=TaskDetailResponse,
    summary="Retrieve task status and concise execution information",
)
async def get_task_by_id(task_id: str) -> TaskDetailResponse:
    """Fetch task information, status, result, and stage history."""
    store = get_task_store()
    task = await store.get_task(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID '{task_id}' not found",
        )
    return TaskDetailResponse(
        task_id=task.task_id,
        user_request=task.user_request,
        selected_agent=task.selected_agent,
        status=task.status,
        created_at=task.created_at,
        updated_at=task.updated_at,
        result=task.result,
        error=task.error,
        approval_required=task.approval_required,
        events=task.events,
    )


@router.get(
    "",
    response_model=List[TaskDetailResponse],
    summary="List recent tasks",
)
async def list_tasks(limit: int = 50) -> List[TaskDetailResponse]:
    """Return recent tasks tracked by the system."""
    store = get_task_store()
    tasks = await store.list_tasks(limit=limit)
    return [
        TaskDetailResponse(
            task_id=t.task_id,
            user_request=t.user_request,
            selected_agent=t.selected_agent,
            status=t.status,
            created_at=t.created_at,
            updated_at=t.updated_at,
            result=t.result,
            error=t.error,
            approval_required=t.approval_required,
            events=t.events,
        )
        for t in tasks
    ]
