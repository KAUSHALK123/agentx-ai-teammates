import logging
from typing import Any, Dict, Optional
from app.services.data_service import IDataService, get_data_service
from app.tools.base import BaseTool, ToolResult
from app.tools.registry import get_tool_registry

logger = logging.getLogger(__name__)


# ==========================================
# 1. Customer Support Tools (READ)
# ==========================================

class LookupCustomerTool(BaseTool):
    """Tool to look up customer profile and contact status."""
    tool_id: str = "lookup_customer"
    name: str = "Customer Lookup"
    description: str = "Find customer account by customer_id, email, phone, or name."
    category: str = "support"
    is_write: bool = False
    input_schema: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "customer_id": {"type": "string", "description": "Customer ID (e.g. CUST-001)"},
            "query": {"type": "string", "description": "Search term (email, phone, or name)"},
        },
    }
    output_schema: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "customer_id": {"type": "string"},
            "name": {"type": "string"},
            "email": {"type": "string"},
            "phone": {"type": "string"},
            "status": {"type": "string"},
        },
    }

    def __init__(self, data_service: Optional[IDataService] = None):
        self.data_service = data_service or get_data_service()

    async def execute(self, **kwargs: Any) -> ToolResult:
        customer_id = kwargs.get("customer_id")
        query = kwargs.get("query") or kwargs.get("email") or kwargs.get("phone")

        if not customer_id and not query:
            return ToolResult(
                success=False,
                tool_id=self.tool_id,
                error="Missing required query parameter",
                message="Provide customer_id or query term to look up customer",
            )

        try:
            cust = None
            if customer_id:
                cust = await self.data_service.get_customer(str(customer_id))
            if not cust and query:
                cust = await self.data_service.find_customer(str(query))

            if not cust:
                if customer_id:
                    return ToolResult(
                        success=False,
                        tool_id=self.tool_id,
                        error="Customer not found",
                        message=f"No customer found matching identifier '{customer_id}'",
                    )
                return ToolResult(
                    success=True,
                    tool_id=self.tool_id,
                    data={"customer": None, "query": query, "status": "no_match"},
                    message=f"Search completed: No customer found matching '{query}'",
                )

            return ToolResult(
                success=True,
                tool_id=self.tool_id,
                data=cust.model_dump(),
                message=f"Found customer {cust.name} ({cust.customer_id})",
            )
        except Exception as exc:
            logger.exception("LookupCustomerTool failed: %s", exc)
            return ToolResult(
                success=False,
                tool_id=self.tool_id,
                error=str(exc),
                message="Error querying customer database",
            )


class LookupOrderTool(BaseTool):
    """Tool to look up order status, items, and delivery details."""
    tool_id: str = "lookup_order"
    name: str = "Order Lookup"
    description: str = "Find order details and fulfillment status by order_id or customer_id."
    category: str = "support"
    is_write: bool = False
    input_schema: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "order_id": {"type": "string", "description": "Order ID (e.g. ORD-1001)"},
            "customer_id": {"type": "string", "description": "Customer ID to list orders for"},
        },
    }

    def __init__(self, data_service: Optional[IDataService] = None):
        self.data_service = data_service or get_data_service()

    async def execute(self, **kwargs: Any) -> ToolResult:
        order_id = kwargs.get("order_id")
        customer_id = kwargs.get("customer_id")

        if not order_id and not customer_id:
            # Check if query parameter has an order token
            query = kwargs.get("query", "")
            if "ORD-" in str(query).upper():
                import re
                match = re.search(r"ORD-\d+", str(query).upper())
                if match:
                    order_id = match.group(0)

        if not order_id and not customer_id:
            return ToolResult(
                success=False,
                tool_id=self.tool_id,
                error="Missing required order parameter",
                message="Provide order_id or customer_id",
            )

        try:
            if order_id:
                order = await self.data_service.get_order(str(order_id))
                if not order:
                    return ToolResult(
                        success=True,
                        tool_id=self.tool_id,
                        data={"found": False, "order_id": str(order_id)},
                        message=f"Order '{order_id}' was not found in records",
                    )
                return ToolResult(
                    success=True,
                    tool_id=self.tool_id,
                    data=order.model_dump(),
                    message=f"Found order {order.order_id} (status: {order.status})",
                )

            orders = await self.data_service.get_orders_for_customer(str(customer_id))
            return ToolResult(
                success=True,
                tool_id=self.tool_id,
                data={"orders": [o.model_dump() for o in orders], "count": len(orders)},
                message=f"Found {len(orders)} orders for customer {customer_id}",
            )
        except Exception as exc:
            logger.exception("LookupOrderTool failed: %s", exc)
            return ToolResult(
                success=False,
                tool_id=self.tool_id,
                error=str(exc),
                message="Error querying orders repository",
            )


class LookupTransactionTool(BaseTool):
    """Tool to inspect payment authorization, gateway reference, and transaction state."""
    tool_id: str = "lookup_transaction"
    name: str = "Transaction Lookup"
    description: str = "Query payment status, amount, and gateway reconciliation by transaction_id or order_id."
    category: str = "support"
    is_write: bool = False
    input_schema: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "transaction_id": {"type": "string", "description": "Transaction ID (e.g. TXN-5001)"},
            "order_id": {"type": "string", "description": "Associated Order ID"},
        },
    }

    def __init__(self, data_service: Optional[IDataService] = None):
        self.data_service = data_service or get_data_service()

    async def execute(self, **kwargs: Any) -> ToolResult:
        tid = kwargs.get("transaction_id") or kwargs.get("order_id")
        if not tid:
            query = kwargs.get("query", "")
            if "TXN-" in str(query).upper():
                import re
                match = re.search(r"TXN-\d+", str(query).upper())
                if match:
                    tid = match.group(0)

        if not tid:
            cid = kwargs.get("customer_id")
            if cid:
                orders = await self.data_service.get_orders_for_customer(str(cid))
                if orders:
                    failed_ord = next((o for o in orders if o.payment_status == "failed"), None)
                    chosen = failed_ord or orders[0]
                    tid = chosen.transaction_id

        if not tid:
            return ToolResult(
                success=False,
                tool_id=self.tool_id,
                error="Missing required transaction identifier",
                message="Provide transaction_id, order_id, or customer_id",
            )


        try:
            txn = await self.data_service.get_transaction(str(tid))
            if not txn:
                return ToolResult(
                    success=True,
                    tool_id=self.tool_id,
                    data={"found": False, "transaction_id": str(tid)},
                    message=f"No transaction found matching '{tid}'",
                )

            return ToolResult(
                success=True,
                tool_id=self.tool_id,
                data=txn.model_dump(),
                message=f"Transaction {txn.transaction_id} is {txn.payment_status} ({txn.currency} {txn.amount})",
            )
        except Exception as exc:
            logger.exception("LookupTransactionTool failed: %s", exc)
            return ToolResult(
                success=False,
                tool_id=self.tool_id,
                error=str(exc),
                message="Error querying transactions store",
            )


# ==========================================
# 2. Sales Tools (READ & WRITE)
# ==========================================

class LookupLeadTool(BaseTool):
    """Tool to inspect sales prospect details and pipeline stage."""
    tool_id: str = "lookup_lead"
    name: str = "Lead Lookup"
    description: str = "Find lead record, company details, and history by lead_id, company, or email."
    category: str = "sales"
    is_write: bool = False
    input_schema: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "lead_id": {"type": "string", "description": "Lead ID (e.g. LEAD-001)"},
            "query": {"type": "string", "description": "Company name or contact search term"},
        },
    }

    def __init__(self, data_service: Optional[IDataService] = None):
        self.data_service = data_service or get_data_service()

    async def execute(self, **kwargs: Any) -> ToolResult:
        lead_id = kwargs.get("lead_id")
        query = kwargs.get("query") or kwargs.get("company") or kwargs.get("inquiry")

        if not lead_id and not query:
            return ToolResult(
                success=False,
                tool_id=self.tool_id,
                error="Missing required lead identifier",
                message="Provide lead_id or query parameter",
            )

        try:
            lead = None
            if lead_id:
                lead = await self.data_service.get_lead(str(lead_id))
            if not lead and query:
                lead = await self.data_service.find_lead(str(query))

            if not lead:
                return ToolResult(
                    success=False,
                    tool_id=self.tool_id,
                    error="Lead not found",
                    message=f"No lead found for '{lead_id or query}'",
                )

            return ToolResult(
                success=True,
                tool_id=self.tool_id,
                data=lead.model_dump(),
                message=f"Found lead {lead.name} ({lead.company}) - Stage: {lead.status}",
            )
        except Exception as exc:
            logger.exception("LookupLeadTool failed: %s", exc)
            return ToolResult(
                success=False,
                tool_id=self.tool_id,
                error=str(exc),
                message="Error looking up sales lead",
            )


class UpdateLeadTool(BaseTool):
    """WRITE Tool to update sales lead pipeline status, notes, or qualification."""
    tool_id: str = "update_lead"
    name: str = "Lead Update"
    description: str = "Modify lead status (contacted, qualified, lost) and append notes."
    category: str = "sales"
    is_write: bool = True
    input_schema: Dict[str, Any] = {
        "type": "object",
        "required": ["lead_id"],
        "properties": {
            "lead_id": {"type": "string", "description": "Lead ID to update (e.g. LEAD-001)"},
            "status": {"type": "string", "description": "Updated status: new, contacted, qualified, lost"},
            "notes": {"type": "string", "description": "Notes to append to lead record"},
        },
    }

    def __init__(self, data_service: Optional[IDataService] = None):
        self.data_service = data_service or get_data_service()

    async def execute(self, **kwargs: Any) -> ToolResult:
        lead_id = kwargs.get("lead_id")
        if not lead_id:
            return ToolResult(
                success=False,
                tool_id=self.tool_id,
                error="Missing required 'lead_id'",
                message="'lead_id' is required to update lead",
            )

        status = kwargs.get("status")
        notes = kwargs.get("notes")

        try:
            updated = await self.data_service.update_lead(
                lead_id=str(lead_id),
                status=str(status) if status else None,
                notes=str(notes) if notes else None,
            )
            if not updated:
                return ToolResult(
                    success=False,
                    tool_id=self.tool_id,
                    error="Lead not found",
                    message=f"Cannot update nonexistent lead '{lead_id}'",
                )

            return ToolResult(
                success=True,
                tool_id=self.tool_id,
                data=updated.model_dump(),
                message=f"Successfully updated lead {updated.lead_id} (status: {updated.status})",
            )
        except Exception as exc:
            logger.exception("UpdateLeadTool failed: %s", exc)
            return ToolResult(
                success=False,
                tool_id=self.tool_id,
                error=str(exc),
                message="Error updating sales lead in CRM",
            )


# ==========================================
# 3. Operations Tools (READ)
# ==========================================

class GetBusinessDataTool(BaseTool):
    """Tool to fetch business operational data, throughput metrics, and fulfillment summaries."""
    tool_id: str = "get_business_data"
    name: str = "Business Data Retrieval"
    description: str = "Retrieve aggregated business metrics, orders summary, revenue, and inventory status."
    category: str = "operations"
    is_write: bool = False
    input_schema: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "metric_type": {"type": "string", "default": "daily_summary", "description": "Type of metrics to pull"},
        },
    }

    def __init__(self, data_service: Optional[IDataService] = None):
        self.data_service = data_service or get_data_service()

    async def execute(self, **kwargs: Any) -> ToolResult:
        metric_type = kwargs.get("metric_type", "daily_summary")
        try:
            data = await self.data_service.get_business_data(metric_type=metric_type)
            return ToolResult(
                success=True,
                tool_id=self.tool_id,
                data=data,
                message=f"Retrieved business data metrics for '{metric_type}'",
            )
        except Exception as exc:
            logger.exception("GetBusinessDataTool failed: %s", exc)
            return ToolResult(
                success=False,
                tool_id=self.tool_id,
                error=str(exc),
                message="Error retrieving operational business data",
            )


class VerifyRecordTool(BaseTool):
    """Tool to audit records and check for discrepancies against expected data."""
    tool_id: str = "verify_record"
    name: str = "Record Verification"
    description: str = "Audit database record (order, customer, lead) against expected values."
    category: str = "operations"
    is_write: bool = False
    input_schema: Dict[str, Any] = {
        "type": "object",
        "required": ["record_type", "record_id"],
        "properties": {
            "record_type": {"type": "string", "description": "Type of record: order, transaction, customer, lead"},
            "record_id": {"type": "string", "description": "Record identifier"},
            "expected_fields": {"type": "object", "description": "Expected key-value pairs to verify"},
        },
    }

    def __init__(self, data_service: Optional[IDataService] = None):
        self.data_service = data_service or get_data_service()

    async def execute(self, **kwargs: Any) -> ToolResult:
        record_type = kwargs.get("record_type")
        record_id = kwargs.get("record_id")
        expected_fields = kwargs.get("expected_fields", {})

        if not record_type or not record_id:
            return ToolResult(
                success=False,
                tool_id=self.tool_id,
                error="Missing required parameters",
                message="'record_type' and 'record_id' are required",
            )

        try:
            audit = await self.data_service.verify_record(
                record_type=str(record_type),
                record_id=str(record_id),
                expected_fields=expected_fields,
            )
            return ToolResult(
                success=True,
                tool_id=self.tool_id,
                data=audit,
                message=(
                    "Record verified with 0 discrepancies"
                    if audit.get("matches_expected")
                    else f"Verification flagged discrepancies: {', '.join(audit.get('discrepancies', []))}"
                ),
            )
        except Exception as exc:
            logger.exception("VerifyRecordTool failed: %s", exc)
            return ToolResult(
                success=False,
                tool_id=self.tool_id,
                error=str(exc),
                message="Error verifying record",
            )


# ==========================================
# 4. General Tools (WRITE)
# ==========================================

class CreateActivityTool(BaseTool):
    """WRITE Tool to append a structured activity log entry to a task."""
    tool_id: str = "create_activity"
    name: str = "Activity Creation"
    description: str = "Log a structured business activity record (note, audit, status change) tied to a task."
    category: str = "general"
    is_write: bool = True
    input_schema: Dict[str, Any] = {
        "type": "object",
        "required": ["task_id", "description"],
        "properties": {
            "task_id": {"type": "string", "description": "Task ID associated with activity"},
            "type": {"type": "string", "default": "note", "description": "Type of activity: note, call, email, status_change, audit"},
            "description": {"type": "string", "description": "Detailed activity description"},
        },
    }

    def __init__(self, data_service: Optional[IDataService] = None):
        self.data_service = data_service or get_data_service()

    async def execute(self, **kwargs: Any) -> ToolResult:
        task_id = kwargs.get("task_id", "task_general")
        activity_type = kwargs.get("type", "note")
        description = kwargs.get("description")

        if not description:
            return ToolResult(
                success=False,
                tool_id=self.tool_id,
                error="Missing required description",
                message="'description' is required to create activity record",
            )

        try:
            record = await self.data_service.create_activity(
                task_id=str(task_id),
                activity_type=str(activity_type),
                description=str(description),
            )
            return ToolResult(
                success=True,
                tool_id=self.tool_id,
                data=record.model_dump(),
                message=f"Logged activity '{record.activity_id}' for task {task_id}",
            )
        except Exception as exc:
            logger.exception("CreateActivityTool failed: %s", exc)
            return ToolResult(
                success=False,
                tool_id=self.tool_id,
                error=str(exc),
                message="Error recording activity log",
            )


def initialize_default_tools() -> None:
    """Register all standard AgentX tools into the global ToolRegistry."""
    from app.tools.support_tools import (
        PrepareCustomerResponseTool,
        IssueDemoRefundTool,
        EscalateSupportCaseTool,
    )
    from app.tools.n8n_tools import (
        SalesProcessLeadTool,
        N8nProcessLeadTool,
        SupportHandleIssueTool,
        N8nSupportHandleIssueTool,
        N8nSendFollowupTool,
        N8nOperationsDailyCheckTool,
    )
    from app.tools.knowledge_tools import LookupKnowledgeTool

    registry = get_tool_registry()
    tools = [
        LookupCustomerTool(),
        LookupOrderTool(),
        LookupTransactionTool(),
        LookupLeadTool(),
        UpdateLeadTool(),
        GetBusinessDataTool(),
        VerifyRecordTool(),
        CreateActivityTool(),
        PrepareCustomerResponseTool(),
        IssueDemoRefundTool(),
        EscalateSupportCaseTool(),
        SalesProcessLeadTool(),
        N8nProcessLeadTool(),
        SupportHandleIssueTool(),
        N8nSupportHandleIssueTool(),
        N8nSendFollowupTool(),
        N8nOperationsDailyCheckTool(),
        LookupKnowledgeTool(),
    ]
    for tool in tools:
        if not registry.has_tool(tool.tool_id):
            registry.register_tool(tool)


# Initialize standard registry on module import
initialize_default_tools()

