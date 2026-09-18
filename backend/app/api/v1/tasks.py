import uuid
from typing import List
from fastapi import APIRouter, HTTPException, status
from app.agents.base import StructuredTaskPlan
from app.agents.router import AgentRouter
from app.models.task import AgentType, Task, TaskStatus
from app.schemas.agent import TaskPlanRequest, TaskPlanResponse
from app.schemas.task import (
    TaskCreateRequest,
    TaskResponse,
    TaskDetailResponse,
)
from app.schemas.execution import (
    TaskExecuteResponse,
    TaskExecutionDetailResponse,
)
from app.services.approval_store import get_approval_store
from app.services.execution_engine import get_execution_engine
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
        input_ids=request.input_ids,
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

    # Save the planned task so it can be executed via POST /tasks/{task_id}/execute
    store = get_task_store()
    agent_type = None
    for at in AgentType:
        if at.value == agent.agent_id:
            agent_type = at
            break
    planned_task = Task(
        task_id=task_id,
        user_request=req_clean,
        selected_agent=agent_type,
        status=TaskStatus.PLANNING,
        plan=plan,
    )
    await store.save_task(planned_task)

    return TaskPlanResponse(
        task_id=task_id,
        selected_agent=agent.agent_id,
        task_category=route_result.task_category,
        confidence=route_result.confidence,
        explanation=route_result.explanation,
        is_ambiguous=False,
        plan=plan,
    )


@router.post(
    "/{task_id}/execute",
    response_model=TaskExecuteResponse,
    summary="Execute a planned business task",
)
async def execute_task(task_id: str) -> TaskExecuteResponse:
    """Execute the existing task plan step-by-step through controlled tools, retries, and verification."""
    store = get_task_store()
    task = await store.get_task(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID '{task_id}' not found",
        )

    # Resolve agent
    agent_id = task.selected_agent.value if task.selected_agent else None
    if not agent_id:
        # Route to agent
        route_result = await _router_instance.determine_route(task.user_request)
        if not route_result.selected_agent:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unable to determine agent for unassigned task.",
            )
        agent_id = route_result.selected_agent
        for at in AgentType:
            if at.value == agent_id:
                task.selected_agent = at
                break

    agent = _router_instance.get_agent(agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Agent '{agent_id}' not found in registry.",
        )

    # Ensure plan exists
    if not task.plan or not task.plan.steps:
        task.plan = await agent.plan(task.user_request, task_id=task.task_id)

    # Execute plan through TaskExecutionEngine
    execution_engine = get_execution_engine()
    executed_task = await execution_engine.execute_task(task, agent, task.plan)
    await store.update_task(executed_task)

    approval_data = None
    if executed_task.status == TaskStatus.WAITING_FOR_APPROVAL and executed_task.result:
        approval_data = executed_task.result.get("approval")
    elif executed_task.current_approval_id:
        appr_store = get_approval_store()
        appr = await appr_store.get_approval(executed_task.current_approval_id)
        if appr:
            approval_data = appr.model_dump()

    return TaskExecuteResponse(
        task_id=executed_task.task_id,
        status=executed_task.status,
        selected_agent=executed_task.selected_agent.value if executed_task.selected_agent else None,
        approval=approval_data,
        final_result=executed_task.result,
        error=executed_task.error,
        message=f"Task execution completed with status: {executed_task.status.value}",
    )


@router.get(
    "/{task_id}/execution",
    response_model=TaskExecutionDetailResponse,
    summary="Retrieve detailed execution trace, step breakdown, and audit records",
)
async def get_task_execution(task_id: str) -> TaskExecutionDetailResponse:
    """Return task execution details including step statuses, tool logs, verification, and final result."""
    store = get_task_store()
    task = await store.get_task(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID '{task_id}' not found",
        )

    steps = task.plan.steps if task.plan else []
    selected_agent_str = task.selected_agent.value if task.selected_agent else None

    approval_data = None
    if task.current_approval_id:
        appr_store = get_approval_store()
        appr = await appr_store.get_approval(task.current_approval_id)
        if appr:
            approval_data = appr.model_dump()
    elif task.result and isinstance(task.result, dict) and "approval" in task.result:
        approval_data = task.result["approval"]

    return TaskExecutionDetailResponse(
        task_id=task.task_id,
        task_status=task.status,
        selected_agent=selected_agent_str,
        current_step=task.current_step_id,
        steps=steps,
        execution_records=task.execution_records,
        verification_status=task.verification_result,
        approval=approval_data,
        final_result=task.result,
        error=task.error,
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
        input_ids=getattr(task, "input_ids", []),
    )


@router.get(
    "/{task_id}/inputs",
    summary="Get all inputs associated with a task",
)
async def get_task_inputs(task_id: str):
    """Return all multimodal inputs attached to this business task."""
    store = get_task_store()
    task = await store.get_task(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID '{task_id}' not found",
        )

    from app.services.input_store import get_input_store
    from app.schemas.input import InputDetailResponse, TaskInputsResponse

    istore = get_input_store()
    inputs = await istore.list_inputs_by_task(task_id)

    for iid in getattr(task, "input_ids", []):
        if iid not in [i.input_id for i in inputs]:
            inp = await istore.get_input(iid)
            if inp:
                inputs.append(inp)

    detail_inputs = [
        InputDetailResponse(
            input_id=i.input_id,
            type=i.type,
            filename=i.filename,
            content_reference=i.content_reference,
            size_bytes=i.size_bytes,
            mime_type=i.mime_type,
            extracted_text=i.extracted_text,
            structured_data=i.structured_data,
            metadata=i.metadata,
            status=i.status,
            error_code=i.error_code,
            error_message=i.error_message,
            task_id=i.task_id,
            created_at=i.created_at,
            updated_at=i.updated_at,
        )
        for i in inputs
    ]

    return TaskInputsResponse(
        task_id=task_id,
        total_inputs=len(detail_inputs),
        inputs=detail_inputs,
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
            input_ids=getattr(t, "input_ids", []),
        )
        for t in tasks
    ]
