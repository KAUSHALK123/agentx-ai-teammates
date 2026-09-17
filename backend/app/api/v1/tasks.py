import uuid
from typing import List
from fastapi import APIRouter, HTTPException, status
from app.agents.base import StructuredTaskPlan
from app.agents.router import AgentRouter
from app.models.task import Task
from app.schemas.agent import TaskPlanRequest, TaskPlanResponse
from app.schemas.task import (
    TaskCreateRequest,
    TaskResponse,
    TaskDetailResponse,
)
from app.services.orchestrator import get_orchestrator
from app.services.task_store import get_task_store

router = APIRouter()
_router_instance = AgentRouter()


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


@router.post(
    "/plan",
    response_model=TaskPlanResponse,
    summary="Generate a structured task plan without execution",
)
async def generate_task_plan(request: TaskPlanRequest) -> TaskPlanResponse:
    """Understand a business request, select the right teammate, and return a structured execution plan."""
    req_clean = request.user_request.strip()
    if not req_clean:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Business request cannot be empty.",
        )

    # 1. Route the request
    route_result = await _router_instance.determine_route(
        user_request=req_clean,
        explicit_agent=request.selected_agent,
    )

    task_id = f"plan_{uuid.uuid4().hex[:12]}"

    # Handle ambiguous requests
    if route_result.is_ambiguous or not route_result.selected_agent:
        return TaskPlanResponse(
            task_id=task_id,
            selected_agent="unassigned",
            task_category=route_result.task_category,
            confidence=route_result.confidence,
            explanation=route_result.explanation,
            is_ambiguous=True,
            clarification_prompt=route_result.clarification_prompt,
            plan=StructuredTaskPlan(
                task_id=task_id,
                agent="unassigned",
                objective="Awaiting user clarification to assign specialized teammate",
                steps=[],
            ),
        )

    # 2. Get the assigned teammate
    agent = _router_instance.get_agent(route_result.selected_agent)

    # 3. Generate structured plan
    plan = await agent.plan(user_request=req_clean, task_id=task_id)

    return TaskPlanResponse(
        task_id=task_id,
        selected_agent=agent.agent_id,
        task_category=route_result.task_category,
        confidence=route_result.confidence,
        explanation=route_result.explanation,
        is_ambiguous=False,
        plan=plan,
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
