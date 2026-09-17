from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from app.schemas.tool import (
    ToolExecutionRequest,
    ToolExecutionResponse,
    ToolMetadataResponse,
)
from app.services.tool_executor import get_tool_executor
from app.tools.registry import get_tool_registry

router = APIRouter()


@router.get(
    "",
    response_model=List[ToolMetadataResponse],
    summary="List all registered tools",
)
async def list_tools(
    category: Optional[str] = Query(None, description="Filter tools by category: support, sales, operations, general"),
) -> List[ToolMetadataResponse]:
    """Return all available tools along with their schemas, categories, and read/write classification."""
    registry = get_tool_registry()
    tools = registry.list_tools(category=category)
    return [
        ToolMetadataResponse(
            tool_id=t.tool_id,
            name=t.name,
            description=t.description,
            category=t.category,
            is_write=t.is_write,
            input_schema=t.input_schema,
            output_schema=t.output_schema,
        )
        for t in tools
    ]


@router.get(
    "/{tool_id}",
    response_model=ToolMetadataResponse,
    summary="Retrieve tool metadata",
)
async def get_tool(tool_id: str) -> ToolMetadataResponse:
    """Return schema and specification for a specific tool."""
    registry = get_tool_registry()
    tool = registry.get_tool(tool_id)
    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool '{tool_id}' not found in registry",
        )
    return ToolMetadataResponse(
        tool_id=tool.tool_id,
        name=tool.name,
        description=tool.description,
        category=tool.category,
        is_write=tool.is_write,
        input_schema=tool.input_schema,
        output_schema=tool.output_schema,
    )


@router.post(
    "/{tool_id}/execute",
    response_model=ToolExecutionResponse,
    summary="Execute tool with permission validation",
)
async def execute_tool(tool_id: str, request: ToolExecutionRequest) -> ToolExecutionResponse:
    """Securely execute a tool under the identity and permissions of the specified agent."""
    executor = get_tool_executor()
    registry = executor.registry

    if not registry.has_tool(tool_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool '{tool_id}' not found in registry",
        )

    # Validate agent permission
    if not executor.has_permission(request.agent_id, tool_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Agent '{request.agent_id}' is not authorized to execute tool '{tool_id}'",
        )

    # Execute tool
    result = await executor.execute_tool(
        tool_id=tool_id,
        agent_id=request.agent_id,
        parameters=request.parameters,
        task_id=request.task_id,
    )

    return ToolExecutionResponse(
        success=result.success,
        tool_id=result.tool_id,
        agent_id=request.agent_id,
        data=result.data,
        error=result.error,
        message=result.message,
    )
