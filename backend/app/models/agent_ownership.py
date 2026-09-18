from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
from app.models.task import AgentType


class AgentMemberRole(str, Enum):
    """Roles for agent membership."""
    OWNER = "OWNER"
    MEMBER = "MEMBER"
    VIEWER = "VIEWER"


class AgentMembershipStatus(str, Enum):
    """Membership status for an agent."""
    ACTIVE = "ACTIVE"
    PENDING = "PENDING"
    REVOKED = "REVOKED"


class AgentInvitationStatus(str, Enum):
    """Status of an agent invitation."""
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    REVOKED = "REVOKED"


class AgentInstance(BaseModel):
    """Domain model representing a specific agent instance owned in a workspace."""

    id: str
    workspace_id: str
    owner_id: str
    name: str
    agent_type: AgentType
    description: str
    status: str = "Online"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AgentMembership(BaseModel):
    """Domain model tracking user permissions for a specific agent instance."""

    agent_id: str
    user_id: str
    role: AgentMemberRole = AgentMemberRole.MEMBER
    status: AgentMembershipStatus = AgentMembershipStatus.ACTIVE
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AgentInvitation(BaseModel):
    """Domain model tracking pending/resolved access invitations for an agent."""

    invitation_id: str
    agent_id: str
    workspace_id: str
    invited_by: str
    user_id: Optional[str] = None
    email: Optional[str] = None
    role: AgentMemberRole = AgentMemberRole.MEMBER
    status: AgentInvitationStatus = AgentInvitationStatus.PENDING
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    resolved_at: Optional[datetime] = None
