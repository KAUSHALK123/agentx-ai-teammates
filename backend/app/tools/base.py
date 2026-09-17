from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pydantic import BaseModel


class ToolResult(BaseModel):
    """Encapsulates the standard output from tool execution."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    message: str
    error: Optional[str] = None


class BaseTool(ABC):
    """Abstract Base Class for all AgentX tools.
    
    Tools act as a controlled intermediary between agents and external services/databases.
    """

    name: str
    description: str

    @abstractmethod
    async def execute(self, **kwargs: Any) -> ToolResult:
        """Execute the tool action against external service layer."""
        pass
