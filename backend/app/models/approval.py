from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional, Union
from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    """Action risk classification."""
    LOW = "LOW"
    HIGH = "HIGH"


class ApprovalStatus(str, Enum):
    """Lifecycle states of an approval request."""
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class ApprovalRecord(BaseModel):
    """Domain model tracking human-in-the-loop approval requests."""
    approval_id: str
    task_id: str
    step_id: Union[int, str]
    agent_id: str
    action: str
    tool_id: Optional[str] = None
    risk_level: RiskLevel = RiskLevel.HIGH
    reason: str
    proposed_input: Dict[str, Any] = Field(default_factory=dict)
    status: ApprovalStatus = ApprovalStatus.PENDING
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    rejection_reason: Optional[str] = None
