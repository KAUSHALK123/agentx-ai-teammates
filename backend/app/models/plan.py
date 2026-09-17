from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class StepStatus(str, Enum):
    """Lifecycle states of an individual plan step."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class AgentCapability(BaseModel):
    """Machine-readable description of an agent capability."""
    name: str
    description: str
    category: str


class PlanStep(BaseModel):
    """Actionable step within a structured task plan."""
    step_id: Union[int, str]
    action: str
    type: str = Field(description="Step type: e.g. investigation, tool_action, verification, synthesis")
    tool_id: Optional[str] = None
    input: Optional[Dict[str, Any]] = None
    status: str = StepStatus.PENDING.value
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result_summary: Optional[str] = None
    error: Optional[str] = None


class StructuredTaskPlan(BaseModel):
    """Structured execution plan for an AI teammate."""
    task_id: str
    agent: str
    objective: str
    steps: List[PlanStep] = Field(default_factory=list)
    primary_tool: Optional[str] = None
    plan_summary: Optional[str] = None

    def model_post_init(self, __context: Any) -> None:
        if not self.plan_summary:
            self.plan_summary = self.objective


# Backward compatibility alias
TaskPlan = StructuredTaskPlan

