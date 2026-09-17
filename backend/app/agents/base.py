from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from app.models.task import AgentType
from app.tools.base import ToolResult
from app.tools.mock_tools import get_tool_by_name


class TaskPlan(BaseModel):
    """Structured execution plan for an AI teammate."""
    steps: List[str]
    primary_tool: Optional[str] = None
    plan_summary: str


class BaseAgent(ABC):
    """Abstract Base Class for all specialized AI teammates."""

    agent_type: AgentType
    name: str
    role: str
    description: str
    available_tools: List[str]

    @abstractmethod
    async def plan(self, user_request: str) -> TaskPlan:
        """Analyze request and generate structured task execution plan."""
        pass

    async def execute_tool(self, tool_name: str, **kwargs: Any) -> ToolResult:
        """Safely invoke an authorized tool through the tool layer."""
        if tool_name not in self.available_tools:
            return ToolResult(
                success=False,
                message=f"Tool '{tool_name}' is not authorized for teammate '{self.name}'",
                error="Unauthorized tool access",
            )
        
        tool = get_tool_by_name(tool_name)
        if not tool:
            return ToolResult(
                success=False,
                message=f"Tool '{tool_name}' not found in registry",
                error="Missing tool implementation",
            )

        return await tool.execute(**kwargs)
