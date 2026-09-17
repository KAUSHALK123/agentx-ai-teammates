from datetime import datetime
from typing import Any, Dict, Optional, Union
from pydantic import BaseModel, Field
from app.models.approval import ApprovalStatus, RiskLevel


class ApprovalResponse(BaseModel):
    """API representation of an approval record."""
    approval_id: str
    task_id: str
    step_id: Union[int, str]
    agent_id: str
    action: str
    tool_id: Optional[str] = None
    risk_level: RiskLevel
    reason: str
    proposed_input: Dict[str, Any] = Field(default_factory=dict)
    status: ApprovalStatus
    created_at: datetime
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    rejection_reason: Optional[str] = None


class ApprovalRejectRequest(BaseModel):
    """Payload for rejecting a pending approval request."""
    reason: Optional[str] = Field(default="Rejected by supervisor", description="Optional reason for rejecting the action")


class ApprovalDecisionResponse(BaseModel):
    """Response returned when an approval request is approved or rejected."""
    approval_id: str
    task_id: str
    status: ApprovalStatus
    message: str
    task_status: Optional[str] = None
    final_result: Optional[Dict[str, Any]] = None
