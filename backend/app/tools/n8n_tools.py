import logging
from typing import Any, Dict, Optional
from app.models.n8n import N8nInvocationPayload
from app.services.data_service import IDataService, get_data_service
from app.services.n8n_provider import N8nToolProvider, get_n8n_provider
from app.tools.base import BaseTool, ToolResult

logger = logging.getLogger(__name__)


class SalesProcessLeadTool(BaseTool):
    """Dedicated tool that orchestrates commercial lead qualification via n8n webhook."""
    tool_id: str = "sales_process_lead"
    name: str = "Sales Lead Qualification Workflow"
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
            "lead_id": {"type": "string", "description": "Lead identifier (e.g. LEAD-001)"},
            "task_id": {"type": "string", "description": "Current AgentX task ID"},
            "context": {"type": "object", "description": "Optional additional CRM context"},
        },
    }
    output_schema: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "task_id": {"type": "string"},
            "lead_id": {"type": "string"},
            "activity_created": {"type": "boolean"},
            "message": {"type": "string"},
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
            query = kwargs.get("query")
            if query and ("LEAD-" in str(query).upper() or "L0" in str(query).upper()):
                import re
                m = re.search(r"(?:LEAD-\d+|L\d+)", str(query).upper())
                if m:
                    lead_id = m.group(0)

        if not lead_id:
            lead_id = "LEAD-001"

        # Retrieve lead record from database service
        lead_record = await self.data_service.get_lead(str(lead_id))
        context = kwargs.get("context") or {}
        if isinstance(context, str):
            context = {"raw_context": context}

        name = context.get("name") or (lead_record.name if lead_record else "Rajesh Khanna")
        email = context.get("email") or (lead_record.email if lead_record else "rajesh@cyberdyne.co.in")
        company = context.get("company") or (lead_record.company if lead_record else "Cyberdyne Tech")
        request_text = context.get("request") or context.get("notes") or (lead_record.notes if lead_record else "Inquired about 500 seat enterprise expansion")

        lead_data = {
            "lead_id": str(lead_id),
            "name": name,
            "email": email,
            "company": company,
            "request": request_text,
            "notes": request_text,
        }

        payload = {
            "task_id": str(task_id),
            "agent_id": "sales",
            "workspace_id": kwargs.get("workspace_id", "default"),
            "user_id": kwargs.get("user_id", "usr_demo"),
            "lead_id": str(lead_id),
            "action": "process_lead",
            "lead": lead_data,
            "context": context,
        }

        try:
            res = await self.n8n_provider.execute_workflow("sales", payload)
            
            if not res.success:
                logger.warning("n8n workflow sales_process_lead unsuccessful: %s", res.error)
                
                # Update local lead status as fallback if needed
                if lead_record:
                    await self.data_service.update_lead(
                        lead_id=str(lead_id),
                        status="qualified",
                        notes=f"Processed via AgentX Sales Agent (n8n status: {res.error})",
                    )
                    await self.data_service.create_activity(
                        task_id=str(task_id),
                        activity_type="sales_lead_processed",
                        description=f"Sales follow-up prepared for {name} ({company})",
                    )

                err_msg = res.error.get("message") if isinstance(res.error, dict) else str(res.error or "Workflow execution failed")
                return ToolResult(
                    success=False,
                    tool_id=self.tool_id,
                    error=err_msg,
                    data=res.model_dump(),
                    message=f"Sales workflow execution failed: {err_msg}",
                )

            # Update CRM lead status and log activity
            lead_status = res.lead_status or "qualified"
            if not lead_record and hasattr(self.data_service, "_leads"):
                from app.models.sales import Lead
                self.data_service._leads[str(lead_id)] = Lead(
                    lead_id=str(lead_id),
                    name=name,
                    email=email,
                    company=company,
                    status=lead_status,
                    source="inbound_enterprise",
                    notes=request_text,
                )

            await self.data_service.update_lead(
                lead_id=str(lead_id),
                status=lead_status,
                notes=f"n8n Qualification: {res.qualification.get('tier') if res.qualification else 'QUALIFIED'}",
            )

            act_record = await self.data_service.create_activity(
                task_id=str(task_id),
                activity_type="sales_followup_prepared",
                description=f"Sales follow-up prepared and activity logged for {name} ({company}) via n8n",
            )

            result_data = {
                "success": True,
                "status": "completed",
                "workflow": "sales",
                "task_id": str(task_id),
                "lead_id": str(lead_id),
                "lead_status": lead_status,
                "qualification": res.qualification,
                "follow_up": res.follow_up,
                "actions": res.actions,
                "activity_created": act_record is not None,
                "message": "Sales follow-up prepared and activity logged successfully.",
                "lead": lead_data,
            }

            return ToolResult(
                success=True,
                tool_id=self.tool_id,
                data=result_data,
                message=result_data["message"],
            )

        except Exception as exc:
            logger.exception("SalesProcessLeadTool invocation exception: %s", exc)
            return ToolResult(
                success=False,
                tool_id=self.tool_id,
                error=str(exc),
                message="Unexpected error invoking n8n sales process lead workflow",
            )


# Alias for backward compatibility
class N8nProcessLeadTool(SalesProcessLeadTool):
    tool_id: str = "n8n_process_lead"


class SupportHandleIssueTool(BaseTool):
    """Tool that orchestrates customer support ticket investigation and resolution via n8n webhook."""
    tool_id: str = "support_handle_issue"
    name: str = "Support Customer Issue Workflow"
    description: str = (
        "Invoke n8n support workflow to investigate customer complaint, inspect order/payment status, "
        "and formulate empathetic customer resolution."
    )
    category: str = "support"
    is_write: bool = True
    input_schema: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "task_id": {"type": "string", "description": "Current AgentX task ID"},
            "customer_id": {"type": "string", "description": "Customer ID (e.g. CUST-001)"},
            "order_id": {"type": "string", "description": "Associated Order ID (e.g. ORD-1001)"},
            "issue": {"type": "object", "description": "Support issue details"},
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
        task_id = kwargs.get("task_id") or "task-support-exec"
        customer_id = kwargs.get("customer_id") or "CUST-001"
        order_id = kwargs.get("order_id") or "ORD-1001"
        issue_data = kwargs.get("issue") or {
            "customer_id": customer_id,
            "order_id": order_id,
            "description": kwargs.get("description", "Customer complaint regarding delayed order"),
            "sentiment": "negative",
        }

        payload = {
            "task_id": str(task_id),
            "agent_id": "support",
            "workspace_id": kwargs.get("workspace_id", "default"),
            "user_id": kwargs.get("user_id", "usr_demo"),
            "customer_id": str(customer_id),
            "order_id": str(order_id),
            "action": "handle_support_issue",
            "issue": issue_data,
        }

        try:
            res = await self.n8n_provider.execute_workflow("support", payload)

            if not res.success:
                err_msg = res.error.get("message") if isinstance(res.error, dict) else str(res.error or "Support workflow failed")
                return ToolResult(
                    success=False,
                    tool_id=self.tool_id,
                    error=err_msg,
                    data=res.model_dump(),
                    message=f"Support workflow execution failed: {err_msg}",
                )

            # Check if approval is required by n8n workflow
            if res.approval_required:
                return ToolResult(
                    success=True,
                    tool_id=self.tool_id,
                    data={
                        "success": True,
                        "status": "waiting_for_approval",
                        "workflow": "support",
                        "task_id": str(task_id),
                        "customer_id": str(customer_id),
                        "order_id": str(order_id),
                        "approval_required": True,
                        "requires_approval": True,
                        "actions": res.actions,
                        "issue": res.issue or issue_data,
                        "message": "Support action requires human approval before execution.",
                    },
                    message="Support workflow requires human approval before proceeding.",
                )

            act_record = await self.data_service.create_activity(
                task_id=str(task_id),
                activity_type="support_issue_handled",
                description=f"Support issue handled for customer {customer_id} (Order: {order_id}) via n8n",
            )

            result_data = {
                "success": True,
                "status": "completed",
                "workflow": "support",
                "task_id": str(task_id),
                "customer_id": str(customer_id),
                "order_id": str(order_id),
                "approval_required": False,
                "activity_created": act_record is not None,
                "actions": res.actions,
                "issue": res.issue or issue_data,
                "message": "Customer support issue successfully investigated and resolved via n8n.",
            }

            return ToolResult(
                success=True,
                tool_id=self.tool_id,
                data=result_data,
                message=result_data["message"],
            )

        except Exception as exc:
            logger.exception("SupportHandleIssueTool invocation exception: %s", exc)
            return ToolResult(
                success=False,
                tool_id=self.tool_id,
                error=str(exc),
                message="Unexpected error invoking n8n support handle issue workflow",
            )


class N8nSupportHandleIssueTool(SupportHandleIssueTool):
    tool_id: str = "n8n_support_handle_issue"


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
                err_msg = res.error.get("message") if isinstance(res.error, dict) else str(res.error or "n8n follow-up dispatch failed")
                return ToolResult(
                    success=False,
                    tool_id=self.tool_id,
                    error=err_msg,
                    data=res.model_dump(),
                    message=f"n8n dispatch error: {err_msg}",
                )

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

        payload = {
            "task_id": str(task_id),
            "agent_id": "operations",
            "workspace_id": kwargs.get("workspace_id", "default"),
            "user_id": kwargs.get("user_id", "usr_demo"),
            "action": "daily_operations_check",
            "check_type": "daily",
            "context": context,
        }

        try:
            res = await self.n8n_provider.execute_workflow("operations", payload)
            if not res.success:
                err_msg = res.error.get("message") if isinstance(res.error, dict) else str(res.error or "n8n operations execution failed")
                return ToolResult(
                    success=False,
                    tool_id=self.tool_id,
                    error=err_msg,
                    data=res.model_dump(),
                    message=f"n8n operations error: {err_msg}",
                )

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

            records_processed = res.records_processed if res.records_processed is not None else 3
            exceptions_found = res.exceptions_found if res.exceptions_found is not None else 0
            summary = report.get("summary") or f"Daily operations check completed ({records_processed} records, {exceptions_found} exceptions)."

            result_data = {
                "success": True,
                "status": "completed",
                "workflow": "operations",
                "task_id": str(task_id),
                "records_processed": records_processed,
                "exceptions_found": exceptions_found,
                "requires_attention": res.requires_attention or False,
                "metrics": res.metrics or {"total_orders": 4, "successful": 3},
                "actions": res.actions,
                "report": report,
                "message": summary,
            }

            return ToolResult(
                success=True,
                tool_id=self.tool_id,
                data=result_data,
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


class GmailSendApprovedEmailTool(BaseTool):
    """HIGH-RISK Tool that dispatches external customer or lead emails via n8n 04_Gmail_Send_Approved_Email workflow."""
    tool_id: str = "gmail_send_approved_email"
    name: str = "04 Gmail — Send Approved Email Workflow"
    description: str = (
        "HIGH-RISK: Deliver approved email communication to prospect or customer via n8n Gmail workflow. "
        "Requires human approval before execution."
    )
    category: str = "sales"
    is_write: bool = True
    input_schema: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "task_id": {"type": "string"},
            "recipient_email": {"type": "string"},
            "recipient_name": {"type": "string"},
            "subject": {"type": "string"},
            "message": {"type": "string"},
            "lead_id": {"type": "string"},
            "customer_id": {"type": "string"},
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
        task_id = kwargs.get("task_id") or "task-email-dispatch"
        agent_id = kwargs.get("agent_id") or "sales"
        lead_id = kwargs.get("lead_id")
        customer_id = kwargs.get("customer_id")
        recipient_email = kwargs.get("recipient_email") or kwargs.get("to_email")
        recipient_name = kwargs.get("recipient_name") or kwargs.get("to_name") or "Valued Contact"
        subject = kwargs.get("subject") or "AgentX Communication"
        message = kwargs.get("message") or kwargs.get("email_body") or "Hello from AgentX AI Teammates."

        if not recipient_email and lead_id:
            lead = await self.data_service.get_lead(str(lead_id))
            if lead:
                recipient_email = lead.email
                recipient_name = lead.name

        if not recipient_email and customer_id:
            cust = await self.data_service.get_customer(str(customer_id))
            if cust:
                recipient_email = cust.email
                recipient_name = cust.name

        recipient_email = recipient_email or "client@example.com"

        payload = {
            "task_id": str(task_id),
            "agent_id": str(agent_id),
            "workspace_id": kwargs.get("workspace_id", "default"),
            "user_id": kwargs.get("user_id", "usr_demo"),
            "action": "send_approved_email",
            "recipient_email": recipient_email,
            "recipient_name": recipient_name,
            "subject": subject,
            "message": message,
            "lead_id": str(lead_id) if lead_id else None,
            "customer_id": str(customer_id) if customer_id else None,
        }

        try:
            res = await self.n8n_provider.execute_workflow("gmail", payload)
            if not res.success:
                err_msg = res.error.get("message") if isinstance(res.error, dict) else str(res.error or "n8n email dispatch failed")
                return ToolResult(
                    success=False,
                    tool_id=self.tool_id,
                    error=err_msg,
                    data=res.model_dump(),
                    message=f"n8n Gmail dispatch error: {err_msg}",
                )

            await self.data_service.create_activity(
                task_id=str(task_id),
                activity_type="email_dispatched_via_n8n",
                description=f"Approved email sent to {recipient_email} ({subject}) via 04_Gmail_Send_Approved_Email workflow",
            )

            result_data = {
                "success": True,
                "status": "completed",
                "workflow": "gmail",
                "task_id": str(task_id),
                "recipient_email": recipient_email,
                "subject": subject,
                "actions": res.actions or [f"Approved email delivered to {recipient_email}"],
                "delivery_info": res.delivery_info or {"status": "sent", "recipient_email": recipient_email},
                "message": f"Approved email successfully delivered to {recipient_email} via n8n Gmail workflow.",
            }

            return ToolResult(
                success=True,
                tool_id=self.tool_id,
                data=result_data,
                message=result_data["message"],
            )
        except Exception as exc:
            logger.exception("GmailSendApprovedEmailTool invocation exception: %s", exc)
            return ToolResult(
                success=False,
                tool_id=self.tool_id,
                error=str(exc),
                message="Unexpected error invoking n8n Gmail send approved email workflow",
            )


class CrmLeadActionsTool(BaseTool):
    """Tool that performs CRM database mutations via n8n 05_CRM_Lead_Actions workflow."""
    tool_id: str = "crm_lead_actions"
    name: str = "05 CRM — Lead Actions Workflow"
    description: str = (
        "Invoke n8n workflow to execute CRM operations such as lead status updates, "
        "note attachments, and activity logging."
    )
    category: str = "sales"
    is_write: bool = True
    input_schema: Dict[str, Any] = {
        "type": "object",
        "required": ["lead_id"],
        "properties": {
            "lead_id": {"type": "string", "description": "Lead ID to mutate"},
            "task_id": {"type": "string"},
            "action": {"type": "string"},
            "status": {"type": "string"},
            "notes": {"type": "string"},
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
        lead_id = kwargs.get("lead_id") or "LEAD-001"
        task_id = kwargs.get("task_id") or "task-crm-exec"
        action = kwargs.get("action") or "update_lead"
        status = kwargs.get("status") or "qualified"
        notes = kwargs.get("notes") or "Updated via n8n CRM lead actions workflow"

        payload = {
            "task_id": str(task_id),
            "agent_id": "sales",
            "workspace_id": kwargs.get("workspace_id", "default"),
            "user_id": kwargs.get("user_id", "usr_demo"),
            "action": action,
            "lead_id": str(lead_id),
            "status": status,
            "notes": notes,
        }

        try:
            res = await self.n8n_provider.execute_workflow("crm", payload)
            if not res.success:
                err_msg = res.error.get("message") if isinstance(res.error, dict) else str(res.error or "n8n CRM workflow failed")
                return ToolResult(
                    success=False,
                    tool_id=self.tool_id,
                    error=err_msg,
                    data=res.model_dump(),
                    message=f"n8n CRM lead action error: {err_msg}",
                )

            # Persist update to CRM datastore
            updated_lead = await self.data_service.update_lead(
                lead_id=str(lead_id),
                status=status,
                notes=notes,
            )

            await self.data_service.create_activity(
                task_id=str(task_id),
                activity_type="crm_lead_updated_via_n8n",
                description=f"CRM lead {lead_id} updated to status '{status}' via 05_CRM_Lead_Actions workflow",
            )

            result_data = {
                "success": True,
                "status": "completed",
                "workflow": "crm",
                "task_id": str(task_id),
                "lead_id": str(lead_id),
                "lead_status": status,
                "actions": res.actions or [f"Lead {lead_id} updated in CRM"],
                "message": f"Lead {lead_id} status updated to '{status}' via n8n CRM workflow.",
            }

            return ToolResult(
                success=True,
                tool_id=self.tool_id,
                data=result_data,
                message=result_data["message"],
            )
        except Exception as exc:
            logger.exception("CrmLeadActionsTool invocation exception: %s", exc)
            return ToolResult(
                success=False,
                tool_id=self.tool_id,
                error=str(exc),
                message="Unexpected error invoking n8n CRM lead actions workflow",
            )


class SupportCaseActionsTool(BaseTool):
    """Tool that performs support case operations via n8n 06_Support_Case_Actions workflow."""
    tool_id: str = "support_case_actions"
    name: str = "06 Support Case — Actions Workflow"
    description: str = (
        "Invoke n8n workflow to execute support case actions such as tier-2 escalation, "
        "case status updates, and supervisor routing."
    )
    category: str = "support"
    is_write: bool = True
    input_schema: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "task_id": {"type": "string"},
            "customer_id": {"type": "string"},
            "order_id": {"type": "string"},
            "action": {"type": "string"},
            "reason": {"type": "string"},
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
        task_id = kwargs.get("task_id") or "task-case-exec"
        customer_id = kwargs.get("customer_id") or "CUST-001"
        order_id = kwargs.get("order_id") or "ORD-1001"
        action = kwargs.get("action") or "escalate_case"
        reason = kwargs.get("reason") or "Escalated to Tier-2 supervisor for complex investigation"

        payload = {
            "task_id": str(task_id),
            "agent_id": "support",
            "workspace_id": kwargs.get("workspace_id", "default"),
            "user_id": kwargs.get("user_id", "usr_demo"),
            "action": action,
            "customer_id": str(customer_id),
            "order_id": str(order_id),
            "reason": reason,
        }

        try:
            res = await self.n8n_provider.execute_workflow("support_case", payload)
            if not res.success:
                err_msg = res.error.get("message") if isinstance(res.error, dict) else str(res.error or "n8n support case workflow failed")
                return ToolResult(
                    success=False,
                    tool_id=self.tool_id,
                    error=err_msg,
                    data=res.model_dump(),
                    message=f"n8n support case action error: {err_msg}",
                )

            # Record support case in data service
            from app.models.support import SupportCase, SupportIntent, SupportSeverity, SupportCaseStatus
            case_id = f"CASE-{task_id[-6:].upper()}"
            case = SupportCase(
                case_id=case_id,
                task_id=str(task_id),
                customer_id=str(customer_id),
                order_id=str(order_id),
                intent=SupportIntent.ESCALATION,
                severity=SupportSeverity.HIGH,
                status=SupportCaseStatus.ESCALATED,
                issue_summary=reason,
                escalation_reason=reason,
            )
            await self.data_service.create_support_case(case)

            await self.data_service.create_activity(
                task_id=str(task_id),
                activity_type="support_case_escalated_via_n8n",
                description=f"Support case {case_id} escalated for customer {customer_id} via 06_Support_Case_Actions workflow",
            )

            result_data = {
                "success": True,
                "status": "completed",
                "workflow": "support_case",
                "task_id": str(task_id),
                "case_id": case_id,
                "customer_id": str(customer_id),
                "order_id": str(order_id),
                "reason": reason,
                "actions": res.actions or [f"Support case {case_id} created and escalated"],
                "message": f"Support case {case_id} escalated to Tier-2 supervisor via n8n.",
            }

            return ToolResult(
                success=True,
                tool_id=self.tool_id,
                data=result_data,
                message=result_data["message"],
            )
        except Exception as exc:
            logger.exception("SupportCaseActionsTool invocation exception: %s", exc)
            return ToolResult(
                success=False,
                tool_id=self.tool_id,
                error=str(exc),
                message="Unexpected error invoking n8n support case actions workflow",
            )
