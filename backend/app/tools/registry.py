import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from app.tools.base import BaseTool, ToolResult

logger = logging.getLogger(__name__)


class IToolProvider(ABC):
    """Interface for pluggable tool sources (Internal, API, or future MCP)."""

    @abstractmethod
    def get_tools(self) -> List[BaseTool]:
        pass


class ToolRegistry:
    """Central registry managing all tools available within the AgentX ecosystem."""

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}

    def register_tool(self, tool: BaseTool) -> None:
        """Register a new tool instance."""
        if not tool.tool_id:
            raise ValueError("Tool must define a non-empty tool_id")
        self._tools[tool.tool_id] = tool
        logger.info("Registered tool '%s' (category=%s, is_write=%s)", tool.tool_id, tool.category, tool.is_write)

    TOOL_ALIASES: Dict[str, str] = {
        "send_customer_email": "gmail_send_approved_email",
        "send_email": "gmail_send_approved_email",
        "gmail_dispatch": "gmail_send_approved_email",
        "n8n_operations_check": "operations_daily_check",
        "n8n_operations_daily_check": "operations_daily_check",
        "n8n_support_case_actions": "support_case_actions",
        "n8n_crm_lead_actions": "crm_lead_actions",
        "n8n_process_lead": "sales_process_lead",
        "n8n_support_handle_issue": "support_handle_issue",
    }

    def _resolve_tool_id(self, tool_id: str) -> str:
        tid = tool_id.strip()
        return self.TOOL_ALIASES.get(tid, tid)

    def get_tool(self, tool_id: str) -> Optional[BaseTool]:
        """Retrieve tool by ID or registered alias."""
        resolved = self._resolve_tool_id(tool_id)
        return self._tools.get(resolved) or self._tools.get(tool_id.strip())

    def has_tool(self, tool_id: str) -> bool:
        """Check whether a tool exists in the registry directly or via alias."""
        resolved = self._resolve_tool_id(tool_id)
        return resolved in self._tools or tool_id.strip() in self._tools


    def list_tools(self, category: Optional[str] = None) -> List[BaseTool]:
        """Return list of all registered tools, optionally filtered by category."""
        tools = list(self._tools.values())
        if category:
            cat = category.strip().lower()
            return [t for t in tools if t.category.lower() == cat]
        return tools

    async def execute_tool(self, tool_id: str, **kwargs) -> ToolResult:
        """Execute a tool directly from the registry."""
        tool = self.get_tool(tool_id)
        if not tool:
            return ToolResult(
                success=False,
                tool_id=tool_id,
                error=f"Tool '{tool_id}' not found in registry",
                message=f"Tool '{tool_id}' is not registered",
            )
        return await tool.execute(**kwargs)


# Global registry instance
_global_registry = ToolRegistry()


def get_tool_registry() -> ToolRegistry:
    """Return configured global tool registry."""
    return _global_registry
