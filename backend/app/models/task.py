from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    """Lifecycle states of an AgentX task."""
    CREATED = "CREATED"
    PLANNING = "PLANNING"
    EXECUTING = "EXECUTING"
    WAITING_FOR_APPROVAL = "WAITING_FOR_APPROVAL"
    VERIFYING = "VERIFYING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    ESCALATED = "ESCALATED"


class AgentType(str, Enum):
    """Available specialized teammate types."""
    SUPPORT = "support"
    SALES = "sales"
    OPERATIONS = "operations"


class ExecutionEvent(BaseModel):
    """Execution event record for auditability without leaking private chain-of-thought."""
    current_stage: TaskStatus
    action_performed: str
    tool_used: Optional[str] = None
    status: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    concise_result_summary: Optional[str] = None


class Task(BaseModel):
    """Core domain model representing an AgentX business task."""
    task_id: str
    user_request: str
    selected_agent: Optional[AgentType] = None
    status: TaskStatus = TaskStatus.CREATED
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    approval_required: bool = False
    events: List[ExecutionEvent] = Field(default_factory=list)

    def add_event(
        self,
        stage: TaskStatus,
        action: str,
        tool_used: Optional[str] = None,
        status: str = "SUCCESS",
        summary: Optional[str] = None,
    ) -> None:
        """Append a concise execution event and update timestamp."""
        event = ExecutionEvent(
            current_stage=stage,
            action_performed=action,
            tool_used=tool_used,
            status=status,
            concise_result_summary=summary,
        )
        self.events.append(event)
        self.status = stage
        self.updated_at = datetime.now(timezone.utc)
