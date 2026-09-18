from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SupportIntent(str, Enum):
    """Standard customer support intents recognized by AgentX."""
    ORDER_ISSUE = "ORDER_ISSUE"
    DELAYED_ORDER = "DELAYED_ORDER"
    PAYMENT_ISSUE = "PAYMENT_ISSUE"
    TRANSACTION_ISSUE = "TRANSACTION_ISSUE"
    REFUND_REQUEST = "REFUND_REQUEST"
    RETURN_REQUEST = "RETURN_REQUEST"
    CUSTOMER_COMPLAINT = "CUSTOMER_COMPLAINT"
    CUSTOMER_REVIEW = "CUSTOMER_REVIEW"
    GENERAL_SUPPORT_QUESTION = "GENERAL_SUPPORT_QUESTION"
    ESCALATION = "ESCALATION"


class SupportSeverity(str, Enum):
    """Explainable support severity classification levels."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class SupportCaseStatus(str, Enum):
    """Lifecycle status of a structured support case."""
    OPEN = "OPEN"
    INVESTIGATING = "INVESTIGATING"
    WAITING_FOR_APPROVAL = "WAITING_FOR_APPROVAL"
    RESOLVED = "RESOLVED"
    ESCALATED = "ESCALATED"
    FAILED = "FAILED"


class ReviewSentiment(str, Enum):
    """Sentiment classification for reviews and customer feedback."""
    POSITIVE = "POSITIVE"
    NEUTRAL = "NEUTRAL"
    NEGATIVE = "NEGATIVE"


class ResponseStrategy(str, Enum):
    """Standard customer response strategies."""
    APOLOGIZE_AND_UPDATE = "Apologize + Provide Update"
    OFFER_COMPENSATION = "Offer Compensation"
    REQUEST_MORE_INFO = "Request More Information"
    ESCALATE = "Escalate"
    CUSTOM_RESPONSE = "Custom Response"


class SupportIntentClassification(BaseModel):
    """Structured intent classification output."""
    intent: SupportIntent
    confidence: float = Field(ge=0.0, le=1.0)
    severity: SupportSeverity
    explanation: str = Field(default="")
    extracted_entities: Dict[str, Any] = Field(default_factory=dict)


class CustomerReviewAnalysis(BaseModel):
    """Structured customer review classification and recommendation."""
    sentiment: ReviewSentiment
    intent: SupportIntent
    severity: SupportSeverity
    recommended_strategy: ResponseStrategy
    available_options: List[str] = Field(default_factory=list)
    draft_response: str
    approval_required: bool = True
    context_found: Optional[Dict[str, Any]] = None


class SupportCase(BaseModel):
    """Structured Support Case abstraction tracking customer inquiry lifecycle."""
    case_id: str
    task_id: str
    customer_id: Optional[str] = None
    order_id: Optional[str] = None
    transaction_id: Optional[str] = None
    intent: SupportIntent
    severity: SupportSeverity
    status: SupportCaseStatus = SupportCaseStatus.OPEN
    issue_summary: str
    resolution: Optional[str] = None
    escalation_reason: Optional[str] = None
    recommended_human_action: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
