from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class WorkspaceRole(str, Enum):
    """Roles within a workspace."""
    OWNER = "OWNER"
    MEMBER = "MEMBER"
    VIEWER = "VIEWER"


class WorkspaceMembershipStatus(str, Enum):
    """Membership status in a workspace."""
    ACTIVE = "ACTIVE"
    PENDING = "PENDING"
    REVOKED = "REVOKED"


class Workspace(BaseModel):
    """Domain model representing a multi-user workspace."""

    id: str
    name: str
    created_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class WorkspaceMembership(BaseModel):
    """Domain model tracking a user's membership in a workspace."""

    workspace_id: str
    user_id: str
    role: WorkspaceRole = WorkspaceRole.MEMBER
    status: WorkspaceMembershipStatus = WorkspaceMembershipStatus.ACTIVE
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
