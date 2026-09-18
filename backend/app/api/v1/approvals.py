from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.agents.router import AgentRouter
from app.models.approval import ApprovalStatus
from app.models.user import User
from app.models.workspace import Workspace
from app.schemas.approval import (
    ApprovalDecisionResponse,
    ApprovalRejectRequest,
    ApprovalResponse,
)
from app.services.approval_store import get_approval_store
from app.services.execution_engine import get_execution_engine
from app.services.task_store import get_task_store
from app.services.auth_service import get_current_user, get_current_workspace, verify_workspace_access, verify_approval_access

router = APIRouter()
_router_instance = AgentRouter()


@router.get(
    "",
    response_model=List[ApprovalResponse],
    summary="List approval requests",
)
async def list_approvals(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by approval status (PENDING, APPROVED, REJECTED)"),
    task_id: Optional[str] = Query(None, description="Filter by task ID"),
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
) -> List[ApprovalResponse]:
    """Retrieve all approval requests in workspace accessible to user."""
    await verify_workspace_access(current_user.id, workspace.id)
    store = get_approval_store()
    st = None
    if status_filter:
        try:
            st = ApprovalStatus(status_filter.upper())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status filter '{status_filter}'. Allowed: PENDING, APPROVED, REJECTED, EXPIRED",
            )

    records = await store.list_approvals(status=st, task_id=task_id)
    filtered = []
    for r in records:
        if getattr(r, "workspace_id", None) and r.workspace_id != workspace.id:
            continue
        filtered.append(r)

    return [
        ApprovalResponse(
            approval_id=r.approval_id,
            task_id=r.task_id,
            step_id=r.step_id,
            agent_id=r.agent_id,
            action=r.action,
            tool_id=r.tool_id,
            risk_level=r.risk_level,
            reason=r.reason,
            proposed_input=r.proposed_input,
            status=r.status,
            created_at=r.created_at,
            resolved_at=r.resolved_at,
            resolved_by=r.resolved_by,
            rejection_reason=r.rejection_reason,
        )
        for r in filtered
    ]


@router.get(
    "/pending",
    response_model=List[ApprovalResponse],
    summary="List pending approval requests",
)
async def list_pending_approvals(
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
) -> List[ApprovalResponse]:
    """Retrieve all pending approval requests in active workspace."""
    await verify_workspace_access(current_user.id, workspace.id)
    store = get_approval_store()
    records = await store.list_approvals(status=ApprovalStatus.PENDING)
    filtered = [r for r in records if getattr(r, "workspace_id", None) == workspace.id or not getattr(r, "workspace_id", None)]

    return [
        ApprovalResponse(
            approval_id=r.approval_id,
            task_id=r.task_id,
            step_id=r.step_id,
            agent_id=r.agent_id,
            action=r.action,
            tool_id=r.tool_id,
            risk_level=r.risk_level,
            reason=r.reason,
            proposed_input=r.proposed_input,
            status=r.status,
            created_at=r.created_at,
            resolved_at=r.resolved_at,
            resolved_by=r.resolved_by,
            rejection_reason=r.rejection_reason,
        )
        for r in filtered
    ]


@router.get(
    "/task/{task_id}",
    response_model=List[ApprovalResponse],
    summary="List approvals for a specific task",
)
async def list_task_approvals(
    task_id: str,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
) -> List[ApprovalResponse]:
    """Retrieve all approval requests associated with a specific task."""
    await verify_workspace_access(current_user.id, workspace.id)
    store = get_approval_store()
    records = await store.list_approvals(task_id=task_id)

    return [
        ApprovalResponse(
            approval_id=r.approval_id,
            task_id=r.task_id,
            step_id=r.step_id,
            agent_id=r.agent_id,
            action=r.action,
            tool_id=r.tool_id,
            risk_level=r.risk_level,
            reason=r.reason,
            proposed_input=r.proposed_input,
            status=r.status,
            created_at=r.created_at,
            resolved_at=r.resolved_at,
            resolved_by=r.resolved_by,
            rejection_reason=r.rejection_reason,
        )
        for r in records
    ]


@router.get(
    "/{approval_id}",
    response_model=ApprovalResponse,
    summary="Retrieve an approval request by ID",
)
async def get_approval_by_id(
    approval_id: str,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
) -> ApprovalResponse:
    """Fetch details and current state for a specific approval record."""
    store = get_approval_store()
    appr = await store.get_approval(approval_id)
    if not appr:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Approval with ID '{approval_id}' not found",
        )

    await verify_approval_access(current_user.id, appr, workspace.id)

    return ApprovalResponse(
        approval_id=appr.approval_id,
        task_id=appr.task_id,
        step_id=appr.step_id,
        agent_id=appr.agent_id,
        action=appr.action,
        tool_id=appr.tool_id,
        risk_level=appr.risk_level,
        reason=appr.reason,
        proposed_input=appr.proposed_input,
        status=appr.status,
        created_at=appr.created_at,
        resolved_at=appr.resolved_at,
        resolved_by=appr.resolved_by,
        rejection_reason=appr.rejection_reason,
    )


@router.post(
    "/{approval_id}/approve",
    response_model=ApprovalDecisionResponse,
    summary="Approve action and resume task execution",
)
async def approve_action(
    approval_id: str,
    resolved_by: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
) -> ApprovalDecisionResponse:
    """Approve a pending high-risk action and immediately resume task execution."""
    approval_store = get_approval_store()
    appr = await approval_store.get_approval(approval_id)
    if not appr:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Approval with ID '{approval_id}' not found",
        )

    await verify_approval_access(current_user.id, appr, workspace.id)

    if appr.status != ApprovalStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Approval '{approval_id}' has already been resolved with status: {appr.status.value}",
        )

    # 1. Update Approval Record
    appr.status = ApprovalStatus.APPROVED
    appr.resolved_at = datetime.now(timezone.utc)
    appr.resolved_by = current_user.id
    await approval_store.update_approval(appr)

    # 2. Fetch Task and Resume Execution
    task_store = get_task_store()
    task = await task_store.get_task(appr.task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Associated task '{appr.task_id}' not found",
        )

    agent_id = appr.agent_id or (task.selected_agent.value if task.selected_agent else "support")
    agent = _router_instance.get_agent(agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent '{agent_id}' not found in router registry",
        )

    execution_engine = get_execution_engine()
    resumed_task = await execution_engine.resume_task_after_approval(task, appr, agent)
    await task_store.update_task(resumed_task)

    return ApprovalDecisionResponse(
        approval_id=appr.approval_id,
        task_id=resumed_task.task_id,
        status=ApprovalStatus.APPROVED,
        message="Action approved and execution resumed",
        task_status=resumed_task.status.value,
        final_result=resumed_task.result,
    )


@router.post(
    "/{approval_id}/reject",
    response_model=ApprovalDecisionResponse,
    summary="Reject action and stop task execution",
)
async def reject_action(
    approval_id: str,
    payload: Optional[ApprovalRejectRequest] = None,
    resolved_by: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
) -> ApprovalDecisionResponse:
    """Reject a proposed high-risk action, preventing execution and stopping the task."""
    approval_store = get_approval_store()
    appr = await approval_store.get_approval(approval_id)
    if not appr:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Approval with ID '{approval_id}' not found",
        )

    await verify_approval_access(current_user.id, appr, workspace.id)

    if appr.status != ApprovalStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Approval '{approval_id}' has already been resolved with status: {appr.status.value}",
        )

    rejection_reason = (payload.reason if payload else None) or "Rejected by supervisor"

    # 1. Update Approval Record
    appr.status = ApprovalStatus.REJECTED
    appr.resolved_at = datetime.now(timezone.utc)
    appr.resolved_by = current_user.id
    appr.rejection_reason = rejection_reason
    await approval_store.update_approval(appr)

    # 2. Fetch Task and Stop Execution
    task_store = get_task_store()
    task = await task_store.get_task(appr.task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Associated task '{appr.task_id}' not found",
        )

    execution_engine = get_execution_engine()
    stopped_task = await execution_engine.stop_task_after_rejection(task, appr, rejection_reason)
    await task_store.update_task(stopped_task)

    return ApprovalDecisionResponse(
        approval_id=appr.approval_id,
        task_id=stopped_task.task_id,
        status=ApprovalStatus.REJECTED,
        message="Action rejected and task execution stopped",
        task_status=stopped_task.status.value,
        final_result=stopped_task.result,
    )
