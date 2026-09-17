from typing import Any, Dict, Optional
from app.tools.base import BaseTool, ToolResult
from app.services.external_services import (
    SupportTicketService,
    SalesCRMService,
    OperationsInventoryService,
)


class TicketLookupTool(BaseTool):
    """Tool to query support tickets via SupportTicketService."""

    name: str = "ticket_lookup"
    description: str = "Looks up ticket status and customer issue details from customer support system."

    async def execute(self, **kwargs: Any) -> ToolResult:
        query = kwargs.get("query", "")
        try:
            ticket = await SupportTicketService.find_ticket(query)
            return ToolResult(
                success=True,
                data=ticket,
                message=f"Retrieved ticket details for '{query}'",
            )
        except Exception as exc:
            return ToolResult(
                success=False,
                message="Failed to query ticket service",
                error=str(exc),
            )


class LeadQualificationTool(BaseTool):
    """Tool to evaluate sales leads via SalesCRMService."""

    name: str = "lead_qualification"
    description: str = "Evaluates sales inquiries and identifies appropriate pricing tier and eligibility."

    async def execute(self, **kwargs: Any) -> ToolResult:
        inquiry = kwargs.get("inquiry", "")
        try:
            qualification = await SalesCRMService.qualify_lead(inquiry)
            return ToolResult(
                success=True,
                data=qualification,
                message="Successfully qualified sales lead and determined tier",
            )
        except Exception as exc:
            return ToolResult(
                success=False,
                message="Failed to qualify lead",
                error=str(exc),
            )


class InventoryStatusTool(BaseTool):
    """Tool to check inventory status via OperationsInventoryService."""

    name: str = "inventory_status"
    description: str = "Queries warehouse ERP for item stock count, SKU information, and fulfillment status."

    async def execute(self, **kwargs: Any) -> ToolResult:
        item = kwargs.get("item", "")
        try:
            stock_info = await OperationsInventoryService.check_inventory(item)
            return ToolResult(
                success=True,
                data=stock_info,
                message=f"Stock info retrieved for '{item}'",
            )
        except Exception as exc:
            return ToolResult(
                success=False,
                message="Failed to query inventory system",
                error=str(exc),
            )


_TOOL_REGISTRY: Dict[str, BaseTool] = {
    TicketLookupTool.name: TicketLookupTool(),
    LeadQualificationTool.name: LeadQualificationTool(),
    InventoryStatusTool.name: InventoryStatusTool(),
}


def get_tool_by_name(name: str) -> Optional[BaseTool]:
    """Retrieve registered tool instance by name."""
    return _TOOL_REGISTRY.get(name)
