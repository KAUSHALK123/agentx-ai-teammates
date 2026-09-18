from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.models.task import AgentType, ExecutionEvent, TaskStatus


class TaskCreateRequest(BaseModel):
    """Schema for initiating an AgentX business task."""
    user_request: str = Field(..., min_length=1, description="Business request or prompt for the AI teammate")
    selected_agent: Optional[str] = Field(None, description="Optional explicit agent override ('support', 'sales', 'operations')")
    input_ids: List[str] = Field(default_factory=list, description="Optional list of uploaded input IDs attached to the task")


class TaskResponse(BaseModel):
    """Initial response returned upon task creation."""
    task_id: str
    selected_agent: Optional[AgentType] = None
    status: TaskStatus


class TaskDetailResponse(BaseModel):
    """Detailed response schema returned when querying a task."""
    task_id: str
    user_request: str
    selected_agent: Optional[AgentType] = None
    status: TaskStatus
    created_at: datetime
    updated_at: datetime
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    approval_required: bool = False
    events: List[ExecutionEvent] = Field(default_factory=list)
    input_ids: List[str] = Field(default_factory=list)


class HealthResponse(BaseModel):
    """System health response schema."""
    status: str
    app_name: str
    version: str
    environment: str
    timestamp: datetime
