from typing import List, Optional
from pydantic import BaseModel, Field
from app.agents.base import AgentCapability, StructuredTaskPlan


class AgentResponse(BaseModel):
    """Schema representing an AI teammate and its capabilities."""
    agent_id: str
    name: str
    role: str
    description: str
    responsibilities: List[str] = Field(default_factory=list)
    capabilities: List[AgentCapability] = Field(default_factory=list)
    available_tools: List[str] = Field(default_factory=list)


class TaskPlanRequest(BaseModel):
    """Request schema for generating a task plan."""
    user_request: str = Field(..., min_length=1, description="Business task or request to plan")
    selected_agent: Optional[str] = Field(None, description="Optional explicit agent override ('support', 'sales', 'operations')")


class TaskPlanResponse(BaseModel):
    """Response schema returned by the planning endpoint."""
    task_id: str
    selected_agent: str
    task_category: str
    confidence: float
    explanation: str
    plan: StructuredTaskPlan
    is_ambiguous: bool = False
    clarification_prompt: Optional[str] = None
