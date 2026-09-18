import uuid
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from app.agents.router import AgentRouter
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceRole, WorkspaceMembership, WorkspaceMembershipStatus
from app.models.agent_ownership import (
    AgentInstance,
    AgentMembership,
    AgentMemberRole,
    AgentMembershipStatus,
    AgentInvitation,
    AgentInvitationStatus,
)
from app.models.task import AgentType
from app.schemas.agent import AgentResponse
from app.schemas.access_control import (
    AgentCreateRequest,
    AgentInstanceResponse,
    AgentMemberResponse,
    AgentInviteRequest,
    AgentInvitationResponse,
)
from app.services.access_control_store import get_access_control_store
from app.services.auth_service import get_current_user, get_current_workspace, verify_workspace_access, verify_agent_access

router = APIRouter()
_router_instance = AgentRouter()
_store = get_access_control_store()


@router.get(
    "",
    response_model=List[AgentResponse],
    summary="List all AI teammates and their capabilities",
)
async def list_agents(
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
) -> List[AgentResponse]:
    """Return specialized AI teammates authorized for the user in the active workspace."""
    # Verify workspace membership
    await verify_workspace_access(current_user.id, workspace.id)

    # Fetch agent instances in workspace where user is active member/owner
    workspace_agents = await _store.list_workspace_agents(workspace.id, user_id=current_user.id)
    
    res = []
    # Include base agent definitions
    for a in _router_instance.list_all_agents():
        # Verify user has access to agent instance if tracked
        ag_instance = await _store.get_agent_instance(a.agent_id)
        if ag_instance:
            # Check user membership
            mem = await _store.get_agent_membership(a.agent_id, current_user.id)
            ws_mem = await _store.get_workspace_membership(workspace.id, current_user.id)
            if not mem and (not ws_mem or ws_mem.role != WorkspaceRole.OWNER):
                continue

        res.append(
            AgentResponse(
                agent_id=a.agent_id,
                name=a.name,
                role=a.role,
                description=a.description,
                responsibilities=a.responsibilities,
                capabilities=a.capabilities,
                available_tools=a.available_tools,
            )
        )
    return res


@router.post(
    "",
    response_model=AgentInstanceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a custom agent instance in workspace",
)
async def create_agent(
    request: AgentCreateRequest,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
) -> AgentInstanceResponse:
    """Create a new agent instance in the workspace with current user as OWNER."""
    await verify_workspace_access(current_user.id, workspace.id, min_role=WorkspaceRole.MEMBER)

    agent_id = f"ag_{uuid.uuid4().hex[:12]}"
    agent = AgentInstance(
        id=agent_id,
        workspace_id=workspace.id,
        owner_id=current_user.id,
        name=request.name.strip(),
        agent_type=request.agent_type,
        description=request.description,
        status="Online",
    )
    created = await _store.create_agent_instance(agent)

    return AgentInstanceResponse(
        id=created.id,
        workspace_id=created.workspace_id,
        owner_id=created.owner_id,
        name=created.name,
        agent_type=created.agent_type,
        description=created.description,
        status=created.status,
        user_role=AgentMemberRole.OWNER,
        created_at=created.created_at,
        updated_at=created.updated_at,
    )


# --- Pending Invitations Endpoints ---

@router.get(
    "/invitations/pending",
    response_model=List[AgentInvitationResponse],
    summary="List pending agent invitations for current user",
)
async def list_pending_invitations(
    current_user: User = Depends(get_current_user),
) -> List[AgentInvitationResponse]:
    """List pending agent access invitations for current user."""
    invitations = await _store.list_pending_invitations_for_user(current_user.id, email=current_user.email)
    return [
        AgentInvitationResponse(
            invitation_id=inv.invitation_id,
            agent_id=inv.agent_id,
            workspace_id=inv.workspace_id,
            invited_by=inv.invited_by,
            user_id=inv.user_id,
            email=inv.email,
            role=inv.role,
            status=inv.status,
            created_at=inv.created_at,
        )
        for inv in invitations
    ]


@router.post(
    "/invitations/{invitation_id}/accept",
    response_model=AgentMemberResponse,
    summary="Accept an agent invitation",
)
async def accept_invitation(
    invitation_id: str,
    current_user: User = Depends(get_current_user),
) -> AgentMemberResponse:
    """Accept pending agent invitation and activate membership."""
    inv = await _store.get_agent_invitation(invitation_id)
    if not inv or inv.status != AgentInvitationStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pending invitation '{invitation_id}' not found.",
        )

    if inv.user_id and inv.user_id != current_user.id and (inv.email and inv.email.lower() != current_user.email.lower()):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Invitation was issued to a different user.",
        )

    # Activate agent membership
    inv.status = AgentInvitationStatus.ACCEPTED
    inv.resolved_at = datetime.now(timezone.utc)
    await _store.update_agent_invitation(inv)

    # Ensure workspace membership is active
    ws_mem = await _store.get_workspace_membership(inv.workspace_id, current_user.id)
    if not ws_mem or ws_mem.status != WorkspaceMembershipStatus.ACTIVE:
        ws_mem = WorkspaceMembership(
            workspace_id=inv.workspace_id,
            user_id=current_user.id,
            role=WorkspaceRole.MEMBER,
            status=WorkspaceMembershipStatus.ACTIVE,
        )
        await _store.save_workspace_membership(ws_mem)

    membership = AgentMembership(
        agent_id=inv.agent_id,
        user_id=current_user.id,
        role=inv.role,
        status=AgentMembershipStatus.ACTIVE,
    )
    saved = await _store.save_agent_membership(membership)

    return AgentMemberResponse(
        agent_id=saved.agent_id,
        user_id=saved.user_id,
        full_name=current_user.full_name,
        email=current_user.email,
        role=saved.role,
        status=saved.status,
        created_at=saved.created_at,
    )


@router.post(
    "/invitations/{invitation_id}/reject",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Reject an agent invitation",
)
async def reject_invitation(
    invitation_id: str,
    current_user: User = Depends(get_current_user),
) -> None:
    """Reject pending agent invitation."""
    inv = await _store.get_agent_invitation(invitation_id)
    if not inv or inv.status != AgentInvitationStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pending invitation '{invitation_id}' not found.",
        )

    inv.status = AgentInvitationStatus.REJECTED
    inv.resolved_at = datetime.now(timezone.utc)
    await _store.update_agent_invitation(inv)


@router.delete(
    "/invitations/{invitation_id}/revoke",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke an agent invitation (Owner only)",
)
async def revoke_invitation(
    invitation_id: str,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
) -> None:
    """Revoke a pending agent invitation (Agent/Workspace Owner only)."""
    inv = await _store.get_agent_invitation(invitation_id)
    if not inv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invitation '{invitation_id}' not found.",
        )

    await verify_agent_access(current_user.id, inv.agent_id, workspace.id, min_role=AgentMemberRole.OWNER)

    inv.status = AgentInvitationStatus.REVOKED
    inv.resolved_at = datetime.now(timezone.utc)
    await _store.update_agent_invitation(inv)


# --- Agent Specific Details & Members ---

@router.get(
    "/{agent_id}",
    response_model=AgentResponse,
    summary="Inspect a specific AI teammate",
)
async def get_agent(
    agent_id: str,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
) -> AgentResponse:
    """Return identity, responsibilities, capabilities, and tools for a specific teammate."""
    # Verify server-side authorization for agent
    await verify_agent_access(current_user.id, agent_id, workspace.id)

    agent = _router_instance.get_agent_by_id(agent_id)
    if not agent:
        # Check custom agent instance
        custom_ag = await _store.get_agent_instance(agent_id)
        if not custom_ag:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Teammate with ID '{agent_id}' not found.",
            )
        base_agent = _router_instance.get_agent(custom_ag.agent_type)
        return AgentResponse(
            agent_id=custom_ag.id,
            name=custom_ag.name,
            role=base_agent.role if base_agent else custom_ag.agent_type.value,
            description=custom_ag.description,
            responsibilities=base_agent.responsibilities if base_agent else [],
            capabilities=base_agent.capabilities if base_agent else [],
            available_tools=base_agent.available_tools if base_agent else [],
        )

    return AgentResponse(
        agent_id=agent.agent_id,
        name=agent.name,
        role=agent.role,
        description=agent.description,
        responsibilities=agent.responsibilities,
        capabilities=agent.capabilities,
        available_tools=agent.available_tools,
    )


@router.get(
    "/{agent_id}/members",
    response_model=List[AgentMemberResponse],
    summary="List agent members",
)
async def list_agent_members(
    agent_id: str,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
) -> List[AgentMemberResponse]:
    """List users who have access to this agent."""
    await verify_agent_access(current_user.id, agent_id, workspace.id)

    memberships = await _store.list_agent_members(agent_id)
    res = []
    for m in memberships:
        u = await _store.get_user(m.user_id)
        res.append(
            AgentMemberResponse(
                agent_id=m.agent_id,
                user_id=m.user_id,
                full_name=u.full_name if u else m.user_id,
                email=u.email if u else None,
                role=m.role,
                status=m.status,
                created_at=m.created_at,
            )
        )
    return res


@router.post(
    "/{agent_id}/members/invite",
    response_model=AgentInvitationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Invite user to agent",
)
async def invite_agent_member(
    agent_id: str,
    request: AgentInviteRequest,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
) -> AgentInvitationResponse:
    """Create an access invitation for an agent (Owner only)."""
    await verify_agent_access(current_user.id, agent_id, workspace.id, min_role=AgentMemberRole.OWNER)

    inv_id = f"inv_{uuid.uuid4().hex[:12]}"
    target_user_id = request.user_id
    if not target_user_id and request.email:
        target_user_id = f"usr_{request.email.split('@')[0].replace('.', '_')}"

    invitation = AgentInvitation(
        invitation_id=inv_id,
        agent_id=agent_id,
        workspace_id=workspace.id,
        invited_by=current_user.id,
        user_id=target_user_id,
        email=request.email,
        role=request.role,
        status=AgentInvitationStatus.PENDING,
    )
    created = await _store.create_agent_invitation(invitation)

    return AgentInvitationResponse(
        invitation_id=created.invitation_id,
        agent_id=created.agent_id,
        workspace_id=created.workspace_id,
        invited_by=created.invited_by,
        user_id=created.user_id,
        email=created.email,
        role=created.role,
        status=created.status,
        created_at=created.created_at,
    )


@router.delete(
    "/{agent_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove agent member",
)
async def remove_agent_member(
    agent_id: str,
    user_id: str,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
) -> None:
    """Revoke user membership from agent (Owner only)."""
    await verify_agent_access(current_user.id, agent_id, workspace.id, min_role=AgentMemberRole.OWNER)
    await _store.remove_agent_membership(agent_id, user_id)
