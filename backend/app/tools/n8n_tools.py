import logging
from typing import Any, Dict, Optional
from app.models.n8n import N8nInvocationPayload
from app.services.data_service import IDataService, get_data_service
from app.services.n8n_provider import N8nToolProvider, get_n8n_provider
from app.tools.base import BaseTool, ToolResult

logger = logging.getLogger(__name__)


class N8nProcessLeadTool(BaseTool):
    """Tool that orchestrates multi-step commercial lead qualification via n8n."""
    tool_id: str = "n8n_process_lead"
    name: str = "n8n Lead Qualification Workflow"
    description: str = (
        "Invoke n8n workflow to assess prospect fit, compute qualification tier, "
        "update CRM lead status, and prepare personalized follow-up outreach."
    )
    category: str = "sales"
    is_write: bool = True
    input_schema: Dict[str, Any] = {
        "type": "object",
        "required": ["lead_id"],
        "properties": {
            "lead_id": {"type": "string", "description": "Lead identifier (e.g. LEAD-001 or L001)"},
            "task_id": {"type": "string", "description": "Current AgentX task ID"},
            "context": {"type": "object", "description": "Optional additional CRM context"},
        },
    }
    output_schema: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "workflow": {"type": "string"},
            "lead_id": {"type": "string"},
            "lead_status": {"type": "string"},
            "qualification": {"type": "object"},
            "follow_up": {"type": "object"},
            "actions": {"type": "array"},
        },
    }

    def __init__(
        self,
        n8n_provider: Optional[N8nToolProvider] = None,
        data_service: Optional[IDataService] = None,
    ):
        self.n8n_provider = n8n_provider or get_n8n_provider()
        self.data_service = data_service or get_data_service()

    async def execute(self, **kwargs: Any) -> ToolResult:
        lead_id = kwargs.get("lead_id")
        task_id = kwargs.get("task_id") or "task-sales-exec"

        if not lead_id:
            # Fallback check for query
            query = kwargs.get("query")
            if query and ("LEAD-" in str(query).upper() or "L0" in str(query).upper()):
                import re
                m = re.search(r"(?:LEAD-\d+|L\d+)", str(query).upper())
                if m:
                    lead_id = m.group(0)

        if not lead_id:
            return ToolResult(
                success=False,
                tool_id=self.tool_id,
                error="Missing required 'lead_id'",
                message="Cannot execute n8n lead workflow without lead_id",
            )

        # Retrieve lead context from data service if not fully provided
        context = kwargs.get("context") or {}
        lead_record = await self.data_service.get_lead(str(lead_id))
        if lead_record:
            if not context.get("name"):
                context["name"] = lead_record.name
            if not context.get("email"):
                context["email"] = lead_record.email
            if not context.get("company"):
                context["company"] = lead_record.company
            if not context.get("source"):
                context["source"] = lead_record.source
            if not context.get("notes"):
                context["notes"] = lead_record.notes

        payload = N8nInvocationPayload(
            task_id=str(task_id),
            agent_id="sales",
            workflow_id="sales_process_lead",
            lead_id=str(lead_id),
            requested_action="process_lead",
            context=context,
        )

        try:
            res = await self.n8n_provider.invoke_workflow(payload)
            if not res.success:
                return ToolResult(
                    success=False,
                    tool_id=self.tool_id,
                    error=res.error or "n8n lead processing failed",
                    data=res.model_dump(),
                    message=f"n8n workflow error: {res.error}",
                )

            # Synchronize lead status in local business data service
            if res.lead_status and lead_record:
                await self.data_service.update_lead(
                    lead_id=str(lead_id),
                    status=res.lead_status,
                    notes=f"n8n Qualification: {res.qualification.get('tier') if res.qualification else 'QUALIFIED'}",
                )

            return ToolResult(
                success=True,
                tool_id=self.tool_id,
                data=res.model_dump(),
                message=f"n8n successfully qualified lead {res.lead_id} (status: {res.lead_status})",
            )
        except Exception as exc:
            logger.exception("N8nProcessLeadTool invocation exception: %s", exc)
            return ToolResult(
                success=False,
                tool_id=self.tool_id,
                error=str(exc),
                message="Unexpected error invoking n8n lead qualification workflow",
            )


class N8nSendFollowupTool(BaseTool):
    """HIGH-RISK Tool that dispatches external customer outreach via n8n after approval."""
    tool_id: str = "n8n_send_followup"
    name: str = "n8n Follow-Up Dispatcher"
    description: str = (
        "HIGH-RISK: Transmit approved commercial follow-up communication to prospect via n8n. "
        "Requires human approval before execution."
    )
    category: str = "sales"
    is_write: bool = True
    input_schema: Dict[str, Any] = {
        "type": "object",
        "required": ["lead_id"],
        "properties": {
            "lead_id": {"type": "string", "description": "Lead ID to contact"},
            "task_id": {"type": "string", "description": "Current AgentX task ID"},
            "follow_up": {"type": "object", "description": "Approved follow-up details (recipient, subject, message)"},
        },
    }
    output_schema: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "workflow": {"type": "string"},
            "delivery_info": {"type": "object"},
            "actions": {"type": "array"},
        },
    }

    def __init__(
        self,
        n8n_provider: Optional[N8nToolProvider] = None,
        data_service: Optional[IDataService] = None,
    ):
        self.n8n_provider = n8n_provider or get_n8n_provider()
        self.data_service = data_service or get_data_service()

    async def execute(self, **kwargs: Any) -> ToolResult:
        lead_id = kwargs.get("lead_id")
        task_id = kwargs.get("task_id") or "task-sales-send"
        follow_up = kwargs.get("follow_up") or {}

        if not lead_id:
            return ToolResult(
                success=False,
                tool_id=self.tool_id,
                error="Missing required 'lead_id'",
                message="Cannot dispatch follow-up without lead_id",
            )

        # If follow_up is not provided in args, check lead context
        if not follow_up.get("recipient_email") or not follow_up.get("subject"):
            lead = await self.data_service.get_lead(str(lead_id))
            if lead:
                follow_up = {
                    "recipient_name": follow_up.get("recipient_name") or lead.name,
                    "recipient_email": follow_up.get("recipient_email") or lead.email,
                    "subject": follow_up.get("subject") or f"AgentX Proposal for {lead.company}",
                    "message": follow_up.get("message") or f"Hello {lead.name}, regarding your {lead.company} expansion inquiry...",
                }

        payload = N8nInvocationPayload(
            task_id=str(task_id),
            agent_id="sales",
            workflow_id="sales_send_followup",
            lead_id=str(lead_id),
            requested_action="send_followup",
            context={"follow_up": follow_up},
        )

        try:
            res = await self.n8n_provider.invoke_workflow(payload)
            if not res.success:
                return ToolResult(
                    success=False,
                    tool_id=self.tool_id,
                    error=res.error or "n8n follow-up dispatch failed",
                    data=res.model_dump(),
                    message=f"n8n dispatch error: {res.error}",
                )

            # Record customer activity
            recipient = res.delivery_info.get("recipient_email") if res.delivery_info else lead_id
            await self.data_service.create_activity(
                task_id=str(task_id),
                activity_type="outreach_dispatched",
                description=f"Follow-up delivered to {recipient} via n8n workflow",
            )

            return ToolResult(
                success=True,
                tool_id=self.tool_id,
                data=res.model_dump(),
                message=f"Follow-up successfully delivered to {recipient} via n8n",
            )
        except Exception as exc:
            logger.exception("N8nSendFollowupTool invocation exception: %s", exc)
            return ToolResult(
                success=False,
                tool_id=self.tool_id,
                error=str(exc),
                message="Unexpected error invoking n8n follow-up dispatch workflow",
            )


class N8nOperationsDailyCheckTool(BaseTool):
    """Tool that orchestrates multi-step daily operations audit and exception detection via n8n."""
    tool_id: str = "n8n_operations_check"
    name: str = "n8n Daily Operational Check Workflow"
    description: str = (
        "Invoke n8n workflow to audit business data feeds, compute operational KPIs, "
        "detect deterministic exceptions, compile status reports, and create follow-up activity records."
    )
    category: str = "operations"
    is_write: bool = True
    input_schema: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "task_id": {"type": "string", "description": "Current AgentX task ID"},
            "category": {"type": "string", "description": "Operational audit category (e.g. daily_summary)"},
            "context": {"type": "object", "description": "Optional additional operational context"},
        },
    }
    output_schema: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "workflow": {"type": "string"},
            "records_processed": {"type": "integer"},
            "exceptions_found": {"type": "integer"},
            "requires_attention": {"type": "boolean"},
            "metrics": {"type": "object"},
            "actions": {"type": "array"},
            "report": {"type": "object"},
        },
    }

    def __init__(
        self,
        n8n_provider: Optional[N8nToolProvider] = None,
        data_service: Optional[IDataService] = None,
    ):
        self.n8n_provider = n8n_provider or get_n8n_provider()
        self.data_service = data_service or get_data_service()

    async def execute(self, **kwargs: Any) -> ToolResult:
        task_id = kwargs.get("task_id") or "task-operations-daily"
        category = kwargs.get("category") or "daily_check"
        context = kwargs.get("context") or {}
        if isinstance(context, str):
            context = {"raw_context": context}

        # Include category in context
        context["category"] = category

        payload = N8nInvocationPayload(
            task_id=str(task_id),
            agent_id="operations",
            workflow_id="operations_daily_business_check",
            requested_action="daily_business_check",
            context=context,
        )

        try:
            res = await self.n8n_provider.invoke_workflow(payload)
            if not res.success:
                return ToolResult(
                    success=False,
                    tool_id=self.tool_id,
                    error=res.error or "n8n operations workflow execution failed",
                    data=res.model_dump(),
                    message=f"n8n operations error: {res.error}",
                )

            # Synchronize created follow-up activities to data service
            report = res.report or {}
            created_activities = report.get("created_activities", [])
            for act in created_activities:
                act_type = act.get("type", "operational_followup")
                target = act.get("target", "system")
                await self.data_service.create_activity(
                    task_id=str(task_id),
                    activity_type=act_type,
                    description=f"Automated follow-up created for {target} via n8n operational workflow",
                )

            summary = report.get("summary") or f"Daily operations check completed ({res.records_processed} records, {res.exceptions_found} exceptions)."

            return ToolResult(
                success=True,
                tool_id=self.tool_id,
                data=res.model_dump(),
                message=summary,
            )
        except Exception as exc:
            logger.exception("N8nOperationsDailyCheckTool invocation exception: %s", exc)
            return ToolResult(
                success=False,
                tool_id=self.tool_id,
                error=str(exc),
                message="Unexpected error invoking n8n daily operations workflow",
            )

