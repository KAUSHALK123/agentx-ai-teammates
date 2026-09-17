from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class ToolResult(BaseModel):
    """Encapsulates the standard output from tool execution."""
    success: bool
    tool_id: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    message: str = ""


class BaseTool(ABC):
    """Abstract Base Class for all AgentX tools.
    
    Tools act as a controlled intermediary between agents and external services/databases.
    Agents never directly access or modify data stores.
    """

    tool_id: str
    name: str
    description: str
    category: str = "general"  # support, sales, operations, general
    is_write: bool = False     # READ vs WRITE tool distinction
    input_schema: Dict[str, Any] = {}
    output_schema: Dict[str, Any] = {}

    @abstractmethod
    async def execute(self, **kwargs: Any) -> ToolResult:
        """Execute the tool action against external service layer."""
        pass
