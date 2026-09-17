from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field


class Customer(BaseModel):
    """Customer entity model."""
    customer_id: str
    name: str
    email: str
    phone: str
    status: str = "active"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class OrderTransaction(BaseModel):
    """Order and Transaction entity model."""
    order_id: str
    customer_id: str
    amount: float
    currency: str = "INR"
    status: str = "confirmed"  # confirmed, pending, delivered, cancelled
    payment_status: str = "successful"  # successful, pending, failed, refunded
    transaction_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Lead(BaseModel):
    """Sales lead entity model."""
    lead_id: str
    name: str
    email: str
    company: str
    status: str = "new"  # new, contacted, qualified, lost
    source: str = "inbound_web"
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ActivityRecord(BaseModel):
    """Business task activity log record."""
    activity_id: str
    task_id: str
    type: str  # note, call, email, status_change, audit
    description: str
    status: str = "completed"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
