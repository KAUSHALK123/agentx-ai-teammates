from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class N8nWorkflowDefinition(BaseModel):
    """Approved n8n workflow definition in the AgentX registry."""
    workflow_id: str
    name: str
    purpose: str
    allowed_agent: str
    risk_level: str = "LOW"
    webhook_path: str
    input_schema: Dict[str, Any] = Field(default_factory=dict)
    output_schema: Dict[str, Any] = Field(default_factory=dict)


class N8nInvocationPayload(BaseModel):
    """Structured payload sent to an n8n webhook."""
    task_id: str
    agent_id: str
    workflow_id: str
    workspace_id: str = "default"
    user_id: str = "usr_demo"
    action: Optional[str] = None
    lead_id: Optional[str] = None
    customer_id: Optional[str] = None
    order_id: Optional[str] = None
    check_type: Optional[str] = None
    requested_action: Optional[str] = None
    lead: Optional[Dict[str, Any]] = None
    issue: Optional[Dict[str, Any]] = None
    context: Dict[str, Any] = Field(default_factory=dict)
    idempotency_key: Optional[str] = None


class N8nExecutionResult(BaseModel):
    """Normalized structured result returned from n8n workflow."""
    success: bool
    status: str = "completed"
    workflow: str
    task_id: Optional[str] = None
    lead_id: Optional[str] = None
    customer_id: Optional[str] = None
    order_id: Optional[str] = None
    approval_required: Optional[bool] = False
    lead_status: Optional[str] = None
    qualification: Optional[Dict[str, Any]] = None
    actions: List[str] = Field(default_factory=list)
    follow_up: Optional[Dict[str, Any]] = None
    delivery_info: Optional[Dict[str, Any]] = None
    records_processed: Optional[int] = None
    exceptions_found: Optional[int] = None
    requires_attention: Optional[bool] = None
    metrics: Optional[Dict[str, Any]] = None
    report: Optional[Dict[str, Any]] = None
    lead: Optional[Dict[str, Any]] = None
    issue: Optional[Dict[str, Any]] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    timestamp: Optional[str] = None


# Whitelist registry of approved AgentX n8n workflows
APPROVED_N8N_WORKFLOWS: Dict[str, N8nWorkflowDefinition] = {
    "sales_process_lead": N8nWorkflowDefinition(
        workflow_id="sales_process_lead",
        name="Sales — Process Lead",
        purpose="Retrieve lead context, evaluate commercial qualification criteria, update CRM status, and draft follow-up.",
        allowed_agent="sales",
        risk_level="LOW",
        webhook_path="agentx-sales-process-lead",
        input_schema={
            "type": "object",
            "required": ["task_id", "lead_id"],
            "properties": {
                "task_id": {"type": "string"},
                "lead_id": {"type": "string"},
                "context": {"type": "object"},
            },
        },
        output_schema={
            "type": "object",
            "required": ["success", "workflow", "lead_id", "lead_status"],
            "properties": {
                "success": {"type": "boolean"},
                "workflow": {"type": "string"},
                "lead_id": {"type": "string"},
                "lead_status": {"type": "string"},
                "actions": {"type": "array"},
                "qualification": {"type": "object"},
                "follow_up": {"type": "object"},
            },
        },
    ),
    "support_handle_issue": N8nWorkflowDefinition(
        workflow_id="support_handle_issue",
        name="Support — Handle Customer Issue",
        purpose="Investigate customer support complaint/order issue, inspect policy limits, and formulate resolution.",
        allowed_agent="support",
        risk_level="LOW",
        webhook_path="agentx-support-handle-issue",
        input_schema={
            "type": "object",
            "required": ["task_id", "customer_id"],
            "properties": {
                "task_id": {"type": "string"},
                "customer_id": {"type": "string"},
                "order_id": {"type": "string"},
                "action": {"type": "string"},
                "issue": {"type": "object"},
            },
        },
        output_schema={
            "type": "object",
            "required": ["success", "workflow"],
            "properties": {
                "success": {"type": "boolean"},
                "workflow": {"type": "string"},
                "approval_required": {"type": "boolean"},
                "actions": {"type": "array"},
                "issue": {"type": "object"},
            },
        },
    ),
    "sales_send_followup": N8nWorkflowDefinition(
        workflow_id="sales_send_followup",
        name="04 Gmail — Send Approved Email",
        purpose="Deliver personalized follow-up communication to a qualified prospect after human approval.",
        allowed_agent="sales",
        risk_level="HIGH",
        webhook_path="agentx-sales-send-followup",
        input_schema={
            "type": "object",
            "required": ["task_id", "lead_id", "follow_up"],
            "properties": {
                "task_id": {"type": "string"},
                "lead_id": {"type": "string"},
                "follow_up": {"type": "object"},
                "approval_token": {"type": "string"},
            },
        },
        output_schema={
            "type": "object",
            "required": ["success", "workflow", "delivery_info"],
            "properties": {
                "success": {"type": "boolean"},
                "workflow": {"type": "string"},
                "lead_id": {"type": "string"},
                "delivery_info": {"type": "object"},
                "actions": {"type": "array"},
            },
        },
    ),
    "gmail_send_approved_email": N8nWorkflowDefinition(
        workflow_id="gmail_send_approved_email",
        name="04 Gmail — Send Approved Email",
        purpose="Transmit approved email outreach to prospect or customer via Gmail n8n integration after human approval.",
        allowed_agent="sales,support",
        risk_level="HIGH",
        webhook_path="agentx-gmail-send-approved-email",
    ),
    "crm_lead_actions": N8nWorkflowDefinition(
        workflow_id="crm_lead_actions",
        name="05 CRM — Lead Actions",
        purpose="Execute CRM database operations such as lead status mutations, note attachments, and commercial activity logging.",
        allowed_agent="sales",
        risk_level="LOW",
        webhook_path="agentx-crm-lead-actions",
    ),
    "support_case_actions": N8nWorkflowDefinition(
        workflow_id="support_case_actions",
        name="06 Support Case — Actions",
        purpose="Execute support case operations such as supervisor escalation, case status updates, and refund logging.",
        allowed_agent="support",
        risk_level="LOW",
        webhook_path="agentx-support-case-actions",
    ),
    "operations_daily_business_check": N8nWorkflowDefinition(
        workflow_id="operations_daily_business_check",
        name="03 Operations — Daily Business Check",
        purpose="Process daily business data feeds, calculate operational metrics, detect exceptions/anomalies, compile status reports, and create follow-up activity records.",
        allowed_agent="operations",
        risk_level="LOW",
        webhook_path="agentx-operations-daily-check",
        input_schema={
            "type": "object",
            "required": ["task_id"],
            "properties": {
                "task_id": {"type": "string"},
                "requested_action": {"type": "string"},
                "context": {"type": "object"},
            },
        },
        output_schema={
            "type": "object",
            "required": ["success", "workflow", "records_processed", "exceptions_found", "requires_attention"],
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
        },
    ),
}


def get_n8n_workflow_definition(workflow_id: str) -> Optional[N8nWorkflowDefinition]:
    """Look up an approved n8n workflow definition."""
    return APPROVED_N8N_WORKFLOWS.get(workflow_id)
