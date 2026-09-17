from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class ToolMetadataResponse(BaseModel):
    """Schema describing tool metadata and parameters."""
    tool_id: str
    name: str
    description: str
    category: str
    is_write: bool = Field(description="Indicates whether tool mutates state (Write) or only inspects data (Read)")
    input_schema: Dict[str, Any] = Field(default_factory=dict)
    output_schema: Dict[str, Any] = Field(default_factory=dict)


class ToolExecutionRequest(BaseModel):
    """Request schema for executing a tool under agent permissions."""
    agent_id: str = Field(..., min_length=1, description="Agent identity requesting execution (e.g. support, sales, operations)")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Input parameters passed to the tool")
    task_id: Optional[str] = Field(None, description="Optional task reference for audit trail")


class ToolExecutionResponse(BaseModel):
    """Response returned after tool execution."""
    success: bool
    tool_id: str
    agent_id: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    message: str = ""
