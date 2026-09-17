from typing import Any, List, Optional
from pydantic import BaseModel, Field


class AgentCapability(BaseModel):
    """Machine-readable description of an agent capability."""
    name: str
    description: str
    category: str


class PlanStep(BaseModel):
    """Actionable step within a structured task plan."""
    step_id: int
    action: str
    type: str = Field(description="Step type: e.g. investigation, tool_action, verification, synthesis")
    status: str = "pending"


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
