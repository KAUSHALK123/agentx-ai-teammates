from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.models.support import (
    CustomerReviewAnalysis,
    ResponseStrategy,
    ReviewSentiment,
    SupportCaseStatus,
    SupportIntent,
    SupportSeverity,
)


class SupportAnalyzeRequest(BaseModel):
    """Request schema for support issue / customer review analysis."""
    message: str = Field(..., description="Customer message, complaint, or review text")
    customer_id: Optional[str] = Field(default=None, description="Optional customer identifier")


class SupportAnalyzeResponse(BaseModel):
    """Response schema returned by the support analysis endpoint."""
    intent: SupportIntent
    confidence: float
    sentiment: Optional[ReviewSentiment] = None
    severity: SupportSeverity
    customer_context: Optional[Dict[str, Any]] = None
    recommended_action: str
    recommended_strategy: Optional[ResponseStrategy] = None
    response_options: List[str] = Field(default_factory=list)
    draft_response: Optional[str] = None
    approval_required: bool = False
    explanation: Optional[str] = None


class SupportCaseResponse(BaseModel):
    """Representation of a support case."""
    case_id: str
    task_id: str
    customer_id: Optional[str] = None
    order_id: Optional[str] = None
    transaction_id: Optional[str] = None
    intent: SupportIntent
    severity: SupportSeverity
    status: SupportCaseStatus
    issue_summary: str
    resolution: Optional[str] = None
    escalation_reason: Optional[str] = None
    recommended_human_action: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class SupportExecuteActionRequest(BaseModel):
    """Request to execute a human-selected response or resolution in Support Review."""
    task_id: Optional[str] = Field(default=None, description="Associated task ID")
    case_id: Optional[str] = Field(default=None, description="Optional support case ID")
    action: str = Field(..., description="Selected response option")
    custom_response: Optional[str] = Field(default=None, description="Optional custom response text")
    customer_id: Optional[str] = Field(default=None, description="Optional customer ID")


class SupportExecuteActionResponse(BaseModel):
    """Result of executing a support action."""
    success: bool
    action: str
    message: str
    case_id: Optional[str] = None
    task_id: Optional[str] = None
    status: str

