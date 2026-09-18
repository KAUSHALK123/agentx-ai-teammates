from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from app.models.task import AgentType
from app.models.workspace import WorkspaceRole, WorkspaceMembershipStatus
from app.models.agent_ownership import AgentMemberRole, AgentMembershipStatus, AgentInvitationStatus


# Workspace Schemas
class WorkspaceCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, description="Workspace display name")


class WorkspaceResponse(BaseModel):
    id: str
    name: str
    created_by: str
    role: Optional[WorkspaceRole] = None
    created_at: datetime
    updated_at: datetime


class WorkspaceMemberResponse(BaseModel):
    workspace_id: str
    user_id: str
    full_name: Optional[str] = None
    email: Optional[str] = None
    role: WorkspaceRole
    status: WorkspaceMembershipStatus
    created_at: datetime


class WorkspaceInviteRequest(BaseModel):
    email: str
    role: WorkspaceRole = WorkspaceRole.MEMBER


# Agent Instance Schemas
class AgentCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, description="Agent display name")
    agent_type: AgentType
    description: str
    responsibilities: Optional[List[str]] = None
    capabilities: Optional[List[str]] = None
    available_tools: Optional[List[str]] = None


class AgentInstanceResponse(BaseModel):
    id: str
    workspace_id: str
    owner_id: str
    name: str
    agent_type: AgentType
    description: str
    status: str
    user_role: Optional[AgentMemberRole] = None
    created_at: datetime
    updated_at: datetime


class AgentMemberResponse(BaseModel):
    agent_id: str
    user_id: str
    full_name: Optional[str] = None
    email: Optional[str] = None
    role: AgentMemberRole
    status: AgentMembershipStatus
    created_at: datetime


class AgentInviteRequest(BaseModel):
    user_id: Optional[str] = None
    email: Optional[str] = None
    role: AgentMemberRole = AgentMemberRole.MEMBER


class AgentInvitationResponse(BaseModel):
    invitation_id: str
    agent_id: str
    workspace_id: str
    invited_by: str
    user_id: Optional[str] = None
    email: Optional[str] = None
    role: AgentMemberRole
    status: AgentInvitationStatus
    created_at: datetime
