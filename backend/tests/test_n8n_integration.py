import pytest
from unittest.mock import patch
import httpx
from app.config.settings import get_settings
from app.services.n8n_provider import N8nToolProvider
from app.services.approval_policy import ApprovalPolicyService
from app.models.approval import RiskLevel
from app.models.n8n import N8nInvocationPayload
from app.tools.n8n_tools import (
    SalesProcessLeadTool,
    SupportHandleIssueTool,
    N8nOperationsDailyCheckTool,
    GmailSendApprovedEmailTool,
    CrmLeadActionsTool,
    SupportCaseActionsTool,
)


@pytest.fixture(autouse=True)
def mock_settings(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("N8N_SALES_WEBHOOK_URL", "http://n8n.local/webhook/sales")
    monkeypatch.setenv("N8N_SUPPORT_WEBHOOK_URL", "http://n8n.local/webhook/support")
    monkeypatch.setenv("N8N_OPERATIONS_WEBHOOK_URL", "http://n8n.local/webhook/operations")
    monkeypatch.setenv("N8N_GMAIL_WEBHOOK_URL", "http://n8n.local/webhook/gmail")
    monkeypatch.setenv("N8N_CRM_WEBHOOK_URL", "http://n8n.local/webhook/crm")
    monkeypatch.setenv("N8N_SUPPORT_CASE_WEBHOOK_URL", "http://n8n.local/webhook/support_case")
    monkeypatch.setenv("N8N_TIMEOUT_SECONDS", "5.0")
    monkeypatch.setenv("N8N_BASE_URL", "http://n8n.local")
    yield
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_resolve_webhook_urls():
    provider = N8nToolProvider()
    assert provider.resolve_webhook_url("sales") == "http://n8n.local/webhook/sales"
    assert provider.resolve_webhook_url("support") == "http://n8n.local/webhook/support"
    assert provider.resolve_webhook_url("operations") == "http://n8n.local/webhook/operations"
    assert provider.resolve_webhook_url("gmail") == "http://n8n.local/webhook/gmail"
    assert provider.resolve_webhook_url("crm") == "http://n8n.local/webhook/crm"
    assert provider.resolve_webhook_url("support_case") == "http://n8n.local/webhook/support_case"


@pytest.mark.asyncio
async def test_01_sales_process_lead_success():
    provider = N8nToolProvider(retry_attempts=0)
    mock_resp_data = {
        "success": True,
        "workflow": "sales",
        "task_id": "task-sales-101",
        "lead_id": "LEAD-001",
        "lead_status": "qualified",
        "qualification": {"tier": "Tier 1 Enterprise"},
        "actions": ["Enriched lead profile", "Updated status to qualified"],
    }

    with patch("httpx.AsyncClient.post", return_value=httpx.Response(200, json=mock_resp_data)):
        tool = SalesProcessLeadTool(n8n_provider=provider)
        res = await tool.execute(task_id="task-sales-101", lead_id="LEAD-001")
        assert res.success is True
        assert res.data["lead_status"] == "qualified"
        assert res.data["workflow"] == "sales"


@pytest.mark.asyncio
async def test_01_sales_process_lead_failure():
    provider = N8nToolProvider(retry_attempts=0)
    with patch("httpx.AsyncClient.post", return_value=httpx.Response(500, text="Internal Server Error")):
        tool = SalesProcessLeadTool(n8n_provider=provider)
        res = await tool.execute(task_id="task-sales-102", lead_id="LEAD-001")
        assert res.success is False
        assert "500" in (res.error or "") or "N8N_HTTP_ERROR" in str(res.error)


@pytest.mark.asyncio
async def test_02_support_handle_issue_success():
    provider = N8nToolProvider(retry_attempts=0)
    mock_resp_data = {
        "success": True,
        "workflow": "support",
        "task_id": "task-supp-201",
        "customer_id": "CUST-001",
        "order_id": "ORD-1001",
        "approval_required": False,
        "actions": ["Investigated order ORD-1001 status", "Generated apology update"],
    }

    with patch("httpx.AsyncClient.post", return_value=httpx.Response(200, json=mock_resp_data)):
        tool = SupportHandleIssueTool(n8n_provider=provider)
        res = await tool.execute(task_id="task-supp-201", customer_id="CUST-001", order_id="ORD-1001")
        assert res.success is True
        assert res.data["status"] == "completed"
        assert res.data["approval_required"] is False


@pytest.mark.asyncio
async def test_02_support_approval_required():
    provider = N8nToolProvider(retry_attempts=0)
    mock_resp_data = {
        "success": True,
        "workflow": "support",
        "task_id": "task-supp-202",
        "customer_id": "CUST-001",
        "order_id": "ORD-1001",
        "approval_required": True,
        "actions": ["Flagged $250 refund exceeding limit"],
    }

    with patch("httpx.AsyncClient.post", return_value=httpx.Response(200, json=mock_resp_data)):
        tool = SupportHandleIssueTool(n8n_provider=provider)
        res = await tool.execute(task_id="task-supp-202", customer_id="CUST-001", order_id="ORD-1001")
        assert res.success is True
        assert res.data["status"] == "waiting_for_approval"
        assert res.data["approval_required"] is True


@pytest.mark.asyncio
async def test_03_operations_daily_check_success():
    provider = N8nToolProvider(retry_attempts=0)
    mock_resp_data = {
        "success": True,
        "workflow": "operations",
        "task_id": "task-ops-301",
        "records_processed": 15,
        "exceptions_found": 1,
        "requires_attention": True,
        "metrics": {"total_orders": 15, "successful": 14},
        "actions": ["Audited warehouse inventory", "Flagged SKU-9012 shortage"],
        "report": {"summary": "Audit complete: 1 SKU below threshold"},
    }

    with patch("httpx.AsyncClient.post", return_value=httpx.Response(200, json=mock_resp_data)):
        tool = N8nOperationsDailyCheckTool(n8n_provider=provider)
        res = await tool.execute(task_id="task-ops-301")
        assert res.success is True
        assert res.data["records_processed"] == 15
        assert res.data["exceptions_found"] == 1


@pytest.mark.asyncio
async def test_04_gmail_send_approved_email_approval_flow():
    """Verify 04_Gmail_Send_Approved_Email requires human approval before sending email."""
    policy = ApprovalPolicyService()
    decision = policy.evaluate(
        agent_id="sales",
        tool_id="gmail_send_approved_email",
        action="Send approved follow-up email to prospect",
    )
    assert decision.approval_required is True
    assert decision.risk_level == RiskLevel.HIGH

    # Execute tool after approval simulation
    provider = N8nToolProvider(retry_attempts=0)
    mock_resp_data = {
        "success": True,
        "workflow": "gmail",
        "task_id": "task-email-401",
        "delivery_info": {"status": "sent", "recipient_email": "rajesh@cyberdyne.co.in"},
        "actions": ["Delivered email to rajesh@cyberdyne.co.in via 04_Gmail_Send_Approved_Email"],
    }

    with patch("httpx.AsyncClient.post", return_value=httpx.Response(200, json=mock_resp_data)):
        tool = GmailSendApprovedEmailTool(n8n_provider=provider)
        res = await tool.execute(
            task_id="task-email-401",
            agent_id="sales",
            lead_id="LEAD-001",
            recipient_email="rajesh@cyberdyne.co.in",
            subject="Proposal Review",
            message="Please find attached our enterprise proposal.",
        )
        assert res.success is True
        assert res.data["recipient_email"] == "rajesh@cyberdyne.co.in"
        assert res.data["workflow"] == "gmail"


@pytest.mark.asyncio
async def test_05_crm_lead_actions_success():
    provider = N8nToolProvider(retry_attempts=0)
    mock_resp_data = {
        "success": True,
        "workflow": "crm",
        "task_id": "task-crm-501",
        "lead_id": "LEAD-001",
        "lead_status": "qualified",
        "actions": ["Updated lead status in CRM via 05_CRM_Lead_Actions"],
    }

    with patch("httpx.AsyncClient.post", return_value=httpx.Response(200, json=mock_resp_data)):
        tool = CrmLeadActionsTool(n8n_provider=provider)
        res = await tool.execute(task_id="task-crm-501", lead_id="LEAD-001", status="qualified", notes="Qualified lead")
        assert res.success is True
        assert res.data["lead_status"] == "qualified"
        assert res.data["workflow"] == "crm"


@pytest.mark.asyncio
async def test_06_support_case_actions_success():
    provider = N8nToolProvider(retry_attempts=0)
    mock_resp_data = {
        "success": True,
        "workflow": "support_case",
        "task_id": "task-case-601",
        "customer_id": "CUST-001",
        "order_id": "ORD-1001",
        "actions": ["Escalated case to Tier-2 supervisor via 06_Support_Case_Actions"],
    }

    with patch("httpx.AsyncClient.post", return_value=httpx.Response(200, json=mock_resp_data)):
        tool = SupportCaseActionsTool(n8n_provider=provider)
        res = await tool.execute(
            task_id="task-case-601",
            customer_id="CUST-001",
            order_id="ORD-1001",
            action="escalate_case",
            reason="Shipment damage complaint requiring refund authorization",
        )
        assert res.success is True
        assert res.data["customer_id"] == "CUST-001"
        assert res.data["workflow"] == "support_case"


@pytest.mark.asyncio
async def test_unauthorized_agent_workflow_rejection():
    """Verify Operations Agent is rejected if attempting to invoke Sales lead workflow."""
    provider = N8nToolProvider(base_url="http://n8n.local")
    payload = N8nInvocationPayload(
        task_id="task-unauth",
        agent_id="operations",
        workflow_id="sales_process_lead",
    )
    res = await provider.invoke_workflow(payload)
    assert res.success is False
    assert "unauthorized" in (res.error or "").lower()


@pytest.mark.asyncio
async def test_timeout_handling():
    provider = N8nToolProvider(retry_attempts=0, timeout=1.0)
    with patch("httpx.AsyncClient.post", side_effect=httpx.TimeoutException("Request timed out")):
        res = await provider.execute_workflow("sales", {"task_id": "task-timeout"})
        assert res.success is False
        assert "N8N_TIMEOUT" in (res.error or "")
        assert res.error_details["code"] == "N8N_TIMEOUT"


@pytest.mark.asyncio
async def test_invalid_response_handling():
    provider = N8nToolProvider(retry_attempts=0)
    with patch("httpx.AsyncClient.post", return_value=httpx.Response(200, text="NOT_VALID_JSON_STRING")):
        res = await provider.execute_workflow("support", {"task_id": "task-invalid"})
        assert res.success is False
        assert "N8N_MALFORMED_RESPONSE" in (res.error or "")


@pytest.mark.asyncio
async def test_missing_configuration_handling():
    provider = N8nToolProvider(retry_attempts=0)
    with patch.object(provider, "resolve_webhook_url", return_value=None):
        res = await provider.execute_workflow("unknown_workflow", {"task_id": "task-missing"})
        assert res.success is False
        assert "N8N_CONFIG_MISSING" in (res.error or "")
