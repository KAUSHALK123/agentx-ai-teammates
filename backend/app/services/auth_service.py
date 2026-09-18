import logging
from typing import Optional
from fastapi import Header, HTTPException, Query, Request, status
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceRole, WorkspaceMembershipStatus
from app.models.agent_ownership import AgentInstance, AgentMemberRole, AgentMembershipStatus
from app.models.task import Task
from app.models.approval import ApprovalRecord
from app.services.access_control_store import get_access_control_store

logger = logging.getLogger(__name__)

DEFAULT_DEMO_USER_ID = "usr_demo_owner"
DEFAULT_DEMO_WORKSPACE_ID = "ws_default"


async def get_current_user(
    request: Request,
    x_user_id: Optional[str] = Header(None, alias="X-User-ID"),
    x_user_email: Optional[str] = Header(None, alias="X-User-Email"),
) -> User:
    """Extract authenticated user identity from request headers or default to demo user."""
    store = get_access_control_store()

    # Check X-User-ID header
    user_id = x_user_id or request.headers.get("X-User-ID") or request.headers.get("x-user-id")
    
    # Check Authorization header (Bearer <user_id>)
    if not user_id:
        auth_header = request.headers.get("Authorization") or request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            user_id = auth_header.split(" ", 1)[1].strip()

    if not user_id:
        user_id = DEFAULT_DEMO_USER_ID

    user = await store.get_user(user_id)
    if not user:
        # Create dynamic user record if novel user ID supplied
        user = User(
            id=user_id,
            email=x_user_email or f"{user_id}@enterprise.internal",
            full_name=user_id.replace("_", " ").title(),
        )
        await store.save_user(user)

    return user


async def get_current_workspace(
    request: Request,
    x_workspace_id: Optional[str] = Header(None, alias="X-Workspace-ID"),
    workspace_id: Optional[str] = Query(None),
) -> Workspace:
    """Extract active workspace context from request headers or default to demo workspace."""
    store = get_access_control_store()
    ws_id = x_workspace_id or workspace_id or request.headers.get("X-Workspace-ID") or request.headers.get("x-workspace-id")
    
    if not ws_id:
        ws_id = DEFAULT_DEMO_WORKSPACE_ID

    workspace = await store.get_workspace(ws_id)
    if not workspace:
        # Fallback to default workspace
        workspace = await store.get_workspace(DEFAULT_DEMO_WORKSPACE_ID)
        if not workspace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workspace '{ws_id}' not found.",
            )

    return workspace


# --- Authorization Enforcement Helpers ---

async def verify_workspace_access(
    user_id: str,
    workspace_id: str,
    min_role: Optional[WorkspaceRole] = None,
) -> Workspace:
    """Server-side check: User belongs to workspace and has required role."""
    store = get_access_control_store()
    ws = await store.get_workspace(workspace_id)
    if not ws:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workspace '{workspace_id}' not found.",
        )

    mem = await store.get_workspace_membership(workspace_id, user_id)
    if not mem or mem.status != WorkspaceMembershipStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied: User '{user_id}' is not an active member of workspace '{workspace_id}'.",
        )

    if min_role:
        role_levels = {WorkspaceRole.VIEWER: 1, WorkspaceRole.MEMBER: 2, WorkspaceRole.OWNER: 3}
        user_level = role_levels.get(mem.role, 0)
        req_level = role_levels.get(min_role, 0)
        if user_level < req_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: Action requires workspace '{min_role.value}' role.",
            )

    return ws


async def verify_agent_access(
    user_id: str,
    agent_id: str,
    workspace_id: str,
    min_role: Optional[AgentMemberRole] = None,
) -> AgentInstance:
    """Server-side check: Agent belongs to workspace AND user has agent permission."""
    store = get_access_control_store()
    
    # 1. Verify workspace membership first
    await verify_workspace_access(user_id, workspace_id)

    # 2. Get agent instance
    agent = await store.get_agent_instance(agent_id)
    if not agent or agent.workspace_id != workspace_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_id}' not found in workspace '{workspace_id}'.",
        )

    # Workspace OWNER always has full access to agents in their workspace
    ws_mem = await store.get_workspace_membership(workspace_id, user_id)
    if ws_mem and ws_mem.role == WorkspaceRole.OWNER:
        return agent

    # 3. Check agent membership
    agent_mem = await store.get_agent_membership(agent_id, user_id)
    if not agent_mem or agent_mem.status != AgentMembershipStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied: User '{user_id}' does not have access to agent '{agent_id}'.",
        )

    if min_role:
        role_levels = {AgentMemberRole.VIEWER: 1, AgentMemberRole.MEMBER: 2, AgentMemberRole.OWNER: 3}
        user_level = role_levels.get(agent_mem.role, 0)
        req_level = role_levels.get(min_role, 0)
        if user_level < req_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: Action requires agent '{min_role.value}' permission.",
            )

    return agent


async def verify_task_access(
    user_id: str,
    task: Task,
    workspace_id: str,
) -> None:
    """Server-side check: Task belongs to workspace AND user has permission to inspect/execute."""
    # 1. Workspace scope match
    if task.workspace_id and task.workspace_id != workspace_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task '{task.task_id}' not found in workspace '{workspace_id}'.",
        )

    # 2. Verify workspace membership
    ws = await verify_workspace_access(user_id, workspace_id)

    # Creator or workspace owner always has task access
    ws_mem = await get_access_control_store().get_workspace_membership(workspace_id, user_id)
    if task.created_by == user_id or (ws_mem and ws_mem.role == WorkspaceRole.OWNER):
        return

    # If task is attached to an agent, check agent membership
    if task.agent_id or task.selected_agent:
        ag_id = task.agent_id or (task.selected_agent.value if hasattr(task.selected_agent, "value") else str(task.selected_agent))
        store = get_access_control_store()
        agent = await store.get_agent_instance(ag_id)
        if agent:
            agent_mem = await store.get_agent_membership(agent.id, user_id)
            if agent_mem and agent_mem.status == AgentMembershipStatus.ACTIVE:
                return

    # If not creator, owner, or agent member, forbid access
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=f"Access denied: User '{user_id}' cannot access task '{task.task_id}'.",
    )


async def verify_approval_access(
    user_id: str,
    approval: ApprovalRecord,
    workspace_id: str,
) -> None:
    """Server-side check: Approval belongs to workspace AND user has permission to resolve."""
    # 1. Check workspace match
    if approval.workspace_id and approval.workspace_id != workspace_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Approval '{approval.approval_id}' not found in workspace '{workspace_id}'.",
        )

    # 2. Verify workspace access (must be MEMBER or OWNER to approve)
    ws_mem = await get_access_control_store().get_workspace_membership(workspace_id, user_id)
    if not ws_mem or ws_mem.status != WorkspaceMembershipStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied: User '{user_id}' is not an active member of workspace '{workspace_id}'.",
        )

    # Task creator cannot auto-approve their own high-risk approval unless they are workspace owner/admin
    if approval.requested_by == user_id and ws_mem.role != WorkspaceRole.OWNER:
        # Check if user is agent owner
        agent_mem = await get_access_control_store().get_agent_membership(approval.agent_id, user_id)
        if not agent_mem or agent_mem.role != AgentMemberRole.OWNER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: Task requester '{user_id}' cannot self-approve high-risk actions without workspace/agent owner sign-off.",
            )
