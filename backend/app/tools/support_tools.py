import logging
import uuid
from typing import Any, Dict, Optional
from app.models.support import (
    ResponseStrategy,
    SupportCase,
    SupportCaseStatus,
    SupportIntent,
    SupportSeverity,
)
from app.services.data_service import IDataService, get_data_service
from app.tools.base import BaseTool, ToolResult

logger = logging.getLogger(__name__)


class PrepareCustomerResponseTool(BaseTool):
    """SAFE Tool to synthesize a contextual customer-facing response draft."""
    tool_id: str = "prepare_customer_response"
    name: str = "Customer Response Preparation"
    description: str = "Prepare and format an empathetic, contextual customer-facing resolution response."
    category: str = "support"
    is_write: bool = False
    input_schema: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "customer_id": {"type": "string", "description": "Target customer ID"},
            "order_id": {"type": "string", "description": "Associated Order ID"},
            "issue_summary": {"type": "string", "description": "Summary of the investigated issue"},
            "proposed_resolution": {"type": "string", "description": "Proposed resolution path"},
            "strategy": {"type": "string", "description": "Communication strategy (e.g. Apologize + Provide Update)"},
        },
    }

    def __init__(self, data_service: Optional[IDataService] = None):
        self.data_service = data_service or get_data_service()

    async def execute(self, **kwargs: Any) -> ToolResult:
        customer_id = kwargs.get("customer_id") or "Valued Customer"
        order_id = kwargs.get("order_id")
        issue = kwargs.get("issue_summary") or "your recent inquiry"
        resolution = kwargs.get("proposed_resolution") or "we have reviewed your account and updated our records"
        strategy = kwargs.get("strategy") or ResponseStrategy.APOLOGIZE_AND_UPDATE.value

        cust = await self.data_service.get_customer(customer_id) if customer_id else None
        cust_name = cust.name if cust else "Valued Customer"

        # Construct contextual professional response
        greeting = f"Hello {cust_name},"
        body = f"Thank you for contacting AgentX Support regarding {issue}."
        if order_id:
            body += f" We have investigated your order {order_id}."
        body += f" Resolution: {resolution}."
        closing = "If you have any further questions, please do not hesitate to reply to this message.\n\nWarm regards,\nAgentX Support Teammate"
        formatted_message = f"{greeting}\n\n{body}\n\n{closing}"

        response_payload = {
            "customer_id": customer_id,
            "customer_name": cust_name,
            "order_id": order_id,
            "issue_summary": issue,
            "proposed_resolution": resolution,
            "strategy": strategy,
            "customer_response": formatted_message,
            "external_dispatch_approved": False,
        }

        return ToolResult(
            success=True,
            tool_id=self.tool_id,
            data=response_payload,
            message=f"Drafted customer response under strategy '{strategy}'",
        )


class IssueDemoRefundTool(BaseTool):
    """HIGH-RISK WRITE Tool to execute a controlled financial refund in the demo ledger."""
    tool_id: str = "issue_demo_refund"
    name: str = "Demo Refund Processing"
    description: str = "Process a financial refund for an order or failed transaction. Requires human approval."
    category: str = "support"
    is_write: bool = True
    input_schema: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "transaction_id": {"type": "string", "description": "Transaction ID to refund"},
            "order_id": {"type": "string", "description": "Order ID associated with refund"},
            "customer_id": {"type": "string", "description": "Customer ID receiving refund"},
            "amount": {"type": "number", "description": "Refund amount"},
            "reason": {"type": "string", "description": "Business justification for refund"},
        },
    }

    def __init__(self, data_service: Optional[IDataService] = None):
        self.data_service = data_service or get_data_service()

    async def execute(self, **kwargs: Any) -> ToolResult:
        txn_id = kwargs.get("transaction_id") or "TXN-5003"
        order_id = kwargs.get("order_id")
        cust_id = kwargs.get("customer_id")
        amount = kwargs.get("amount")
        reason = kwargs.get("reason") or "Customer requested refund for failed transaction"

        try:
            refund_data = await self.data_service.issue_refund(
                transaction_id=str(txn_id),
                amount=float(amount) if amount is not None else None,
                reason=str(reason),
                customer_id=str(cust_id) if cust_id else None,
                order_id=str(order_id) if order_id else None,
            )
            return ToolResult(
                success=True,
                tool_id=self.tool_id,
                data=refund_data,
                message=f"Processed demo refund {refund_data['refund_id']} for INR {refund_data['amount']}",
            )
        except Exception as exc:
            logger.exception("IssueDemoRefundTool failed: %s", exc)
            return ToolResult(
                success=False,
                tool_id=self.tool_id,
                error=str(exc),
                message="Error processing demo refund in ledger",
            )


class EscalateSupportCaseTool(BaseTool):
    """WRITE Tool to formally escalate an unresolved, missing-info, or high-risk case to human tier-2."""
    tool_id: str = "escalate_support_case"
    name: str = "Support Escalation"
    description: str = "Escalate complex, missing-info, or critical cases to human tier-2 supervisors."
    category: str = "support"
    is_write: bool = True
    input_schema: Dict[str, Any] = {
        "type": "object",
        "required": ["reason"],
        "properties": {
            "task_id": {"type": "string", "description": "Associated task ID"},
            "customer_id": {"type": "string", "description": "Customer ID"},
            "reason": {"type": "string", "description": "Detailed reason for escalation"},
            "severity": {"type": "string", "default": "HIGH", "description": "Escalation severity level"},
            "recommended_human_action": {"type": "string", "description": "Recommended action for human operator"},
        },
    }

    def __init__(self, data_service: Optional[IDataService] = None):
        self.data_service = data_service or get_data_service()

    async def execute(self, **kwargs: Any) -> ToolResult:
        task_id = kwargs.get("task_id") or f"task_{uuid.uuid4().hex[:8]}"
        customer_id = kwargs.get("customer_id")
        reason = kwargs.get("reason") or "Case requires manual human investigation"
        severity_str = str(kwargs.get("severity", "HIGH")).upper()
        severity = getattr(SupportSeverity, severity_str, SupportSeverity.HIGH)
        rec_action = kwargs.get("recommended_human_action") or "Contact customer directly and investigate ledger"

        case_id = f"case_{uuid.uuid4().hex[:10]}"
        case = SupportCase(
            case_id=case_id,
            task_id=str(task_id),
            customer_id=str(customer_id) if customer_id else None,
            intent=SupportIntent.ESCALATION,
            severity=severity,
            status=SupportCaseStatus.ESCALATED,
            issue_summary=reason,
            escalation_reason=reason,
            recommended_human_action=rec_action,
        )

        try:
            saved_case = await self.data_service.create_support_case(case)
            escalation_payload = {
                "escalated": True,
                "case_id": saved_case.case_id,
                "task_id": saved_case.task_id,
                "customer_id": saved_case.customer_id,
                "reason": reason,
                "severity": severity.value,
                "recommended_human_action": rec_action,
            }
            return ToolResult(
                success=True,
                tool_id=self.tool_id,
                data=escalation_payload,
                message=f"Escalated support case {case_id}: {reason}",
            )
        except Exception as exc:
            logger.exception("EscalateSupportCaseTool failed: %s", exc)
            return ToolResult(
                success=False,
                tool_id=self.tool_id,
                error=str(exc),
                message="Failed to record case escalation",
            )
