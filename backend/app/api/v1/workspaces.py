import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMembership, WorkspaceRole, WorkspaceMembershipStatus
from app.schemas.access_control import (
    WorkspaceCreateRequest,
    WorkspaceResponse,
    WorkspaceMemberResponse,
    WorkspaceInviteRequest,
)
from app.services.access_control_store import get_access_control_store
from app.services.auth_service import get_current_user, verify_workspace_access

router = APIRouter()
_store = get_access_control_store()


@router.get("", response_model=List[WorkspaceResponse], summary="List user's active workspaces")
async def list_workspaces(current_user: User = Depends(get_current_user)) -> List[WorkspaceResponse]:
    """Return all workspaces where the user has an active membership."""
    workspaces = await _store.list_user_workspaces(current_user.id)
    res = []
    for ws in workspaces:
        mem = await _store.get_workspace_membership(ws.id, current_user.id)
        res.append(
            WorkspaceResponse(
                id=ws.id,
                name=ws.name,
                created_by=ws.created_by,
                role=mem.role if mem else WorkspaceRole.MEMBER,
                created_at=ws.created_at,
                updated_at=ws.updated_at,
            )
        )
    return res


@router.post("", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED, summary="Create a workspace")
async def create_workspace(
    request: WorkspaceCreateRequest,
    current_user: User = Depends(get_current_user),
) -> WorkspaceResponse:
    """Create a new multi-user workspace with current user as OWNER."""
    ws_id = f"ws_{uuid.uuid4().hex[:12]}"
    workspace = Workspace(
        id=ws_id,
        name=request.name.strip(),
        created_by=current_user.id,
    )
    created = await _store.create_workspace(workspace)
    return WorkspaceResponse(
        id=created.id,
        name=created.name,
        created_by=created.created_by,
        role=WorkspaceRole.OWNER,
        created_at=created.created_at,
        updated_at=created.updated_at,
    )


@router.get("/{workspace_id}", response_model=WorkspaceResponse, summary="Inspect workspace details")
async def get_workspace(
    workspace_id: str,
    current_user: User = Depends(get_current_user),
) -> WorkspaceResponse:
    """Get workspace profile if user is authorized."""
    ws = await verify_workspace_access(current_user.id, workspace_id)
    mem = await _store.get_workspace_membership(workspace_id, current_user.id)
    return WorkspaceResponse(
        id=ws.id,
        name=ws.name,
        created_by=ws.created_by,
        role=mem.role if mem else WorkspaceRole.MEMBER,
        created_at=ws.created_at,
        updated_at=ws.updated_at,
    )


@router.get("/{workspace_id}/members", response_model=List[WorkspaceMemberResponse], summary="List workspace members")
async def list_workspace_members(
    workspace_id: str,
    current_user: User = Depends(get_current_user),
) -> List[WorkspaceMemberResponse]:
    """List members of a workspace."""
    await verify_workspace_access(current_user.id, workspace_id)
    memberships = await _store.list_workspace_members(workspace_id)
    res = []
    for m in memberships:
        user_info = await _store.get_user(m.user_id)
        res.append(
            WorkspaceMemberResponse(
                workspace_id=m.workspace_id,
                user_id=m.user_id,
                full_name=user_info.full_name if user_info else m.user_id,
                email=user_info.email if user_info else None,
                role=m.role,
                status=m.status,
                created_at=m.created_at,
            )
        )
    return res


@router.post("/{workspace_id}/members/invite", response_model=WorkspaceMemberResponse, summary="Invite member to workspace")
async def invite_workspace_member(
    workspace_id: str,
    request: WorkspaceInviteRequest,
    current_user: User = Depends(get_current_user),
) -> WorkspaceMemberResponse:
    """Invite or add a user to the workspace (OWNER only)."""
    await verify_workspace_access(current_user.id, workspace_id, min_role=WorkspaceRole.OWNER)
    
    # Resolve or create user ID by email reference
    target_user_id = f"usr_{request.email.split('@')[0].replace('.', '_')}"
    target_user = await _store.get_user(target_user_id)
    if not target_user:
        target_user = User(
            id=target_user_id,
            email=request.email,
            full_name=request.email.split('@')[0].replace('.', ' ').title(),
        )
        await _store.save_user(target_user)

    mem = WorkspaceMembership(
        workspace_id=workspace_id,
        user_id=target_user.id,
        role=request.role,
        status=WorkspaceMembershipStatus.ACTIVE,
    )
    saved = await _store.save_workspace_membership(mem)
    return WorkspaceMemberResponse(
        workspace_id=saved.workspace_id,
        user_id=saved.user_id,
        full_name=target_user.full_name,
        email=target_user.email,
        role=saved.role,
        status=saved.status,
        created_at=saved.created_at,
    )


@router.delete("/{workspace_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Remove workspace member")
async def remove_workspace_member(
    workspace_id: str,
    user_id: str,
    current_user: User = Depends(get_current_user),
) -> None:
    """Revoke user membership from workspace (OWNER only)."""
    await verify_workspace_access(current_user.id, workspace_id, min_role=WorkspaceRole.OWNER)
    
    mem = await _store.get_workspace_membership(workspace_id, user_id)
    if mem:
        mem.status = WorkspaceMembershipStatus.REVOKED
        await _store.save_workspace_membership(mem)
