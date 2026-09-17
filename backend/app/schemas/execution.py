from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field
from app.models.plan import PlanStep
from app.models.task import TaskStatus


class TaskExecutionRecordSchema(BaseModel):
    """Execution record for an individual tool invocation."""
    execution_id: str
    task_id: str
    agent_id: str
    step_id: Optional[Union[int, str]] = None
    tool_id: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    input_summary: str
    result_summary: str
    error: Optional[str] = None


class VerificationSummary(BaseModel):
    """Structured verification summary within final result."""
    verified: bool
    verification_type: Optional[str] = "record_match"
    summary: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class TaskFinalResult(BaseModel):
    """Structured final task completion payload."""
    task_id: str
    status: TaskStatus
    summary: str
    actions_performed: List[str] = Field(default_factory=list)
    verification: VerificationSummary


class TaskExecutionDetailResponse(BaseModel):
    """Comprehensive execution details schema for GET /tasks/{task_id}/execution."""
    task_id: str
    task_status: TaskStatus
    selected_agent: Optional[str] = None
    current_step: Optional[Union[int, str]] = None
    steps: List[PlanStep] = Field(default_factory=list)
    execution_records: List[Dict[str, Any]] = Field(default_factory=list)
    verification_status: Optional[Dict[str, Any]] = None
    approval: Optional[Dict[str, Any]] = None
    final_result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class TaskExecuteResponse(BaseModel):
    """Response schema for POST /tasks/{task_id}/execute."""
    task_id: str
    status: TaskStatus
    selected_agent: Optional[str] = None
    approval: Optional[Dict[str, Any]] = None
    final_result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    message: str
