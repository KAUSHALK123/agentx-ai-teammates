import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set
from pydantic import BaseModel, Field
from app.models.task import AgentType
from app.tools.base import ToolResult
from app.tools.registry import ToolRegistry, get_tool_registry

logger = logging.getLogger(__name__)


class ToolExecutionRecord(BaseModel):
    """Structured audit record for a tool execution."""
    execution_id: str
    task_id: Optional[str] = None
    agent_id: str
    tool_id: str
    status: str  # SUCCESS, FAILED, PERMISSION_DENIED, INVALID_INPUT
    started_at: datetime
    completed_at: datetime
    input_summary: str
    result_summary: Optional[str] = None
    error: Optional[str] = None


class ToolExecutionService:
    """Orchestrates secure tool execution, validating permissions, schemas, and logging audit records."""

    # Explicit agent permissions matrix
    _PERMISSIONS: Dict[str, Set[str]] = {
        AgentType.SUPPORT.value: {
            "lookup_customer",
            "lookup_order",
            "lookup_transaction",
            "create_activity",
            "prepare_customer_response",
            "issue_demo_refund",
            "escalate_support_case",
        },
        AgentType.SALES.value: {
            "lookup_customer",
            "lookup_lead",
            "update_lead",
            "create_activity",
            "n8n_process_lead",
            "n8n_send_followup",
        },
        AgentType.OPERATIONS.value: {
            "get_business_data",
            "verify_record",
            "create_activity",
            "n8n_operations_check",
        },
    }

    def __init__(self, registry: Optional[ToolRegistry] = None):
        self.registry = registry or get_tool_registry()
        self._execution_history: List[ToolExecutionRecord] = []
        self._lock = asyncio.Lock()

    def get_agent_permissions(self, agent_id: str) -> Set[str]:
        """Return allowed tool IDs for a given agent."""
        return self._PERMISSIONS.get(agent_id.strip().lower(), set())

    def has_permission(self, agent_id: str, tool_id: str) -> bool:
        """Verify whether an agent has authorization to execute a tool."""
        allowed = self.get_agent_permissions(agent_id)
        return tool_id.strip() in allowed

    async def execute_tool(
        self,
        tool_id: str,
        agent_id: str,
        parameters: Optional[Dict[str, Any]] = None,
        task_id: Optional[str] = None,
    ) -> ToolResult:
        """Execute a tool through permission verification, input validation, and audit recording."""
        started_at = datetime.now(timezone.utc)
        execution_id = f"exec_{uuid.uuid4().hex[:12]}"
        clean_params = parameters or {}
        input_summary = f"params_keys={list(clean_params.keys())}"

        # 1. Verify tool exists in registry
        tool = self.registry.get_tool(tool_id)
        if not tool:
            err = f"Tool '{tool_id}' not found in registry"
            await self._record_log(
                execution_id=execution_id,
                task_id=task_id,
                agent_id=agent_id,
                tool_id=tool_id,
                status="FAILED",
                started_at=started_at,
                input_summary=input_summary,
                error=err,
            )
            return ToolResult(
                success=False,
                tool_id=tool_id,
                error=err,
                message=err,
            )

        # 2. Check agent authorization
        if not self.has_permission(agent_id, tool_id):
            err = f"Agent '{agent_id}' is not authorized to use tool '{tool_id}'"
            logger.warning("Permission denied: %s", err)
            await self._record_log(
                execution_id=execution_id,
                task_id=task_id,
                agent_id=agent_id,
                tool_id=tool_id,
                status="PERMISSION_DENIED",
                started_at=started_at,
                input_summary=input_summary,
                error=err,
            )
            return ToolResult(
                success=False,
                tool_id=tool_id,
                error=err,
                message="Permission denied: Agent cannot execute this tool",
            )

        # 3. Basic schema validation (required fields)
        required_fields = tool.input_schema.get("required", [])
        missing_fields = [f for f in required_fields if f not in clean_params or clean_params[f] is None]
        if missing_fields:
            err = f"Missing required parameters: {', '.join(missing_fields)}"
            await self._record_log(
                execution_id=execution_id,
                task_id=task_id,
                agent_id=agent_id,
                tool_id=tool_id,
                status="INVALID_INPUT",
                started_at=started_at,
                input_summary=input_summary,
                error=err,
            )
            return ToolResult(
                success=False,
                tool_id=tool_id,
                error=err,
                message=err,
            )

        # 4. Controlled tool execution
        try:
            result = await tool.execute(**clean_params)
            await self._record_log(
                execution_id=execution_id,
                task_id=task_id,
                agent_id=agent_id,
                tool_id=tool_id,
                status="SUCCESS" if result.success else "FAILED",
                started_at=started_at,
                input_summary=input_summary,
                result_summary=result.message[:120] if result.message else None,
                error=result.error,
            )
            return result
        except Exception as exc:
            logger.exception("Unexpected exception executing tool %s: %s", tool_id, exc)
            await self._record_log(
                execution_id=execution_id,
                task_id=task_id,
                agent_id=agent_id,
                tool_id=tool_id,
                status="FAILED",
                started_at=started_at,
                input_summary=input_summary,
                error=str(exc),
            )
            return ToolResult(
                success=False,
                tool_id=tool_id,
                error=str(exc),
                message="Tool execution failed due to an internal error",
            )

    async def _record_log(
        self,
        execution_id: str,
        task_id: Optional[str],
        agent_id: str,
        tool_id: str,
        status: str,
        started_at: datetime,
        input_summary: str,
        result_summary: Optional[str] = None,
        error: Optional[str] = None,
    ) -> None:
        """Append an execution audit log entry."""
        record = ToolExecutionRecord(
            execution_id=execution_id,
            task_id=task_id,
            agent_id=agent_id,
            tool_id=tool_id,
            status=status,
            started_at=started_at,
            completed_at=datetime.now(timezone.utc),
            input_summary=input_summary,
            result_summary=result_summary,
            error=error,
        )
        async with self._lock:
            self._execution_history.append(record)

    async def get_execution_logs(self, limit: int = 50) -> List[ToolExecutionRecord]:
        """Return recent tool execution audit records."""
        async with self._lock:
            return list(reversed(self._execution_history))[:limit]


# Global singleton instance
_tool_executor_instance: Optional[ToolExecutionService] = None


def get_tool_executor() -> ToolExecutionService:
    """Return configured tool execution service."""
    global _tool_executor_instance
    if _tool_executor_instance is None:
        _tool_executor_instance = ToolExecutionService()
    return _tool_executor_instance
