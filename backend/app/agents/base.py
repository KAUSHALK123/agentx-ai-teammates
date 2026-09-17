from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.models.task import AgentType
from app.models.plan import AgentCapability, PlanStep, StructuredTaskPlan, TaskPlan
from app.tools.base import ToolResult


class BaseAgent(ABC):
    """Abstract Base Class for all specialized AI teammates."""

    agent_id: str
    agent_type: AgentType
    name: str
    role: str
    description: str
    responsibilities: List[str] = Field(default_factory=list)
    capabilities: List[AgentCapability] = Field(default_factory=list)
    system_instructions: str = ""
    available_tools: List[str] = Field(default_factory=list)

    @abstractmethod
    async def plan(self, user_request: str, task_id: Optional[str] = None) -> StructuredTaskPlan:
        """Analyze business request and generate a structured execution plan."""
        pass

    async def execute(self, action: str, **kwargs: Any) -> Dict[str, Any]:
        """Execute a planned step or action hook."""
        return {
            "status": "completed",
            "action": action,
            "agent_id": self.agent_id,
            "details": kwargs,
        }

    async def execute_tool(self, tool_name: str, **kwargs: Any) -> ToolResult:
        """Safely invoke an authorized tool through the tool execution service."""
        from app.services.tool_executor import get_tool_executor
        executor = get_tool_executor()
        return await executor.execute_tool(
            tool_id=tool_name,
            agent_id=self.agent_id,
            parameters=kwargs,
        )
