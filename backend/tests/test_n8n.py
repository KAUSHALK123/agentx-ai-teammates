import pytest
import httpx
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.config.settings import get_settings
from app.models.task import Task, TaskStatus, AgentType
from app.models.plan import PlanStep, StructuredTaskPlan
from app.models.approval import ApprovalStatus
from app.models.n8n import (
    APPROVED_N8N_WORKFLOWS,
    N8nInvocationPayload,
    N8nExecutionResult,
    get_n8n_workflow_definition,
)
from app.services.n8n_provider import N8nToolProvider
from app.services.data_service import get_data_service
from app.services.execution_engine import TaskExecutionEngine
from app.agents.sales_agent import SalesAgent
from app.tools.n8n_tools import N8nProcessLeadTool, N8nSendFollowupTool


client = TestClient(app)


# ==============================================================
# 1. Configuration & Registry Tests
# ==============================================================

def test_n8n_configuration():
    """Verify n8n configuration defaults and properties."""
    settings = get_settings()
    assert settings.n8n_base_url is not None
    assert "localhost" in settings.n8n_base_url
    assert settings.n8n_webhook_timeout_seconds > 0
    assert settings.n8n_retry_attempts >= 1


def test_approved_n8n_workflow_registry():
    """Verify approved workflows are registered with appropriate schemas and permissions."""
    assert "sales_process_lead" in APPROVED_N8N_WORKFLOWS
    assert "sales_send_followup" in APPROVED_N8N_WORKFLOWS

    wf_lead = get_n8n_workflow_definition("sales_process_lead")
    assert wf_lead is not None
    assert wf_lead.allowed_agent == "sales"
    assert wf_lead.risk_level == "LOW"
    assert wf_lead.webhook_path == "agentx-sales-process-lead"

    wf_send = get_n8n_workflow_definition("sales_send_followup")
    assert wf_send is not None
    assert wf_send.allowed_agent == "sales"
    assert wf_send.risk_level == "HIGH"
    assert wf_send.webhook_path == "agentx-sales-send-followup"


def test_unapproved_workflow_rejected():
    """Verify that unapproved workflow IDs are rejected by the registry check."""
    assert get_n8n_workflow_definition("arbitrary_workflow_999") is None


# ==============================================================
# 2. N8N Tool Provider Unit Tests (Mocked HTTP Layer)
# ==============================================================

@pytest.mark.asyncio
async def test_n8n_provider_unapproved_workflow():
    """Verify provider rejects unapproved workflows without making HTTP calls."""
    provider = N8nToolProvider(base_url="http://mock-n8n:5678")
    payload = N8nInvocationPayload(
        task_id="t1",
        agent_id="sales",
        workflow_id="unknown_workflow",
        requested_action="hack",
    )
    res = await provider.invoke_workflow(payload)
    assert res.success is False
    assert "N8N_VALIDATION_ERROR" in (res.error or "")


@pytest.mark.asyncio
async def test_n8n_provider_unauthorized_agent():
    """Verify provider rejects unauthorized agents (e.g. support invoking sales_process_lead)."""
    provider = N8nToolProvider(base_url="http://mock-n8n:5678")
    payload = N8nInvocationPayload(
        task_id="t2",
        agent_id="support",  # Unauthorized: only 'sales' allowed
        workflow_id="sales_process_lead",
        requested_action="process_lead",
    )
    res = await provider.invoke_workflow(payload)
    assert res.success is False
    assert "unauthorized" in (res.error or "").lower()


@pytest.mark.asyncio
async def test_n8n_provider_success_invocation():
    """Verify provider properly parses a successful n8n response contract."""
    provider = N8nToolProvider(base_url="http://mock-n8n:5678")

    mock_n8n_response = {
        "success": True,
        "workflow": "sales_process_lead",
        "task_id": "task_100",
        "lead_id": "LEAD-001",
        "lead_status": "qualified",
        "qualification": {
            "score": 88,
            "tier": "TIER_1_ENTERPRISE",
            "status": "qualified",
            "rationale": "High-value enterprise prospect with 500+ seat potential",
        },
        "actions": [
            "Lead context retrieved",
            "Qualification scored",
            "Proposal drafted",
        ],
        "follow_up": {
            "prepared": True,
            "subject": "Enterprise Proposal",
            "message": "Hello Rajesh...",
        },
    }

    payload = N8nInvocationPayload(
        task_id="task_100",
        agent_id="sales",
        workflow_id="sales_process_lead",
        lead_id="LEAD-001",
        requested_action="process_lead",
    )

    with patch("httpx.AsyncClient.post") as mock_post:
        mock_post.return_value = httpx.Response(200, json=mock_n8n_response)

        res = await provider.invoke_workflow(payload)
        assert res.success is True
        assert res.workflow == "sales_process_lead"
        assert res.lead_status == "qualified"
        assert res.qualification["score"] == 88
        assert res.follow_up["prepared"] is True


@pytest.mark.asyncio
async def test_n8n_provider_idempotency_cache():
    """Verify duplicate invocations return cached result without hitting n8n twice."""
    provider = N8nToolProvider(base_url="http://mock-n8n:5678")

    payload = N8nInvocationPayload(
        task_id="task_idempotent",
        agent_id="sales",
        workflow_id="sales_process_lead",
        lead_id="LEAD-001",
        requested_action="process_lead",
    )

    mock_response = {
        "success": True,
        "workflow": "sales_process_lead",
        "lead_status": "qualified",
        "qualification": {"score": 90, "tier": "TIER_1_ENTERPRISE"},
    }

    with patch("httpx.AsyncClient.post") as mock_post:
        mock_post.return_value = httpx.Response(200, json=mock_response)

        # First call hits mock HTTP
        res1 = await provider.invoke_workflow(payload)
        assert res1.success is True
        assert mock_post.call_count == 1

        # Second identical call must be served from cache
        res2 = await provider.invoke_workflow(payload)
        assert res2.success is True
        assert mock_post.call_count == 1  # Not incremented


@pytest.mark.asyncio
async def test_n8n_provider_connection_unavailable():
    """Verify clear N8N_UNAVAILABLE error when n8n cannot be reached."""
    provider = N8nToolProvider(base_url="http://invalid-n8n-host:9999", retry_attempts=0)

    payload = N8nInvocationPayload(
        task_id="task_unavail",
        agent_id="sales",
        workflow_id="sales_process_lead",
        requested_action="process_lead",
    )

    with patch("httpx.AsyncClient.post", side_effect=httpx.ConnectError("Connection refused")):
        res = await provider.invoke_workflow(payload)
        assert res.success is False
        assert "N8N_UNAVAILABLE" in (res.error or "")


@pytest.mark.asyncio
async def test_n8n_provider_timeout_handling():
    """Verify clear N8N_TIMEOUT error when request times out."""
    provider = N8nToolProvider(base_url="http://mock-n8n:5678", timeout=1.0, retry_attempts=0)

    payload = N8nInvocationPayload(
        task_id="task_timeout",
        agent_id="sales",
        workflow_id="sales_process_lead",
        requested_action="process_lead",
    )

    with patch("httpx.AsyncClient.post", side_effect=httpx.TimeoutException("Read timeout")):
        res = await provider.invoke_workflow(payload)
        assert res.success is False
        assert "N8N_TIMEOUT" in (res.error or "")


@pytest.mark.asyncio
async def test_n8n_provider_malformed_json_response():
    """Verify clear N8N_MALFORMED_RESPONSE when n8n returns unparseable content."""
    provider = N8nToolProvider(base_url="http://mock-n8n:5678", retry_attempts=0)

    payload = N8nInvocationPayload(
        task_id="task_malformed",
        agent_id="sales",
        workflow_id="sales_process_lead",
        requested_action="process_lead",
    )

    with patch("httpx.AsyncClient.post") as mock_post:
        mock_post.return_value = httpx.Response(200, content=b"invalid json")

        res = await provider.invoke_workflow(payload)
        assert res.success is False
        assert "N8N_MALFORMED_RESPONSE" in (res.error or "")


# ==============================================================
# 3. Sales Teammate Planning Tests
# ==============================================================

@pytest.mark.asyncio
async def test_sales_agent_plans_lead_processing():
    """Verify Sales Agent automatically formulates an n8n workflow execution plan for lead requests."""
    sales = SalesAgent()
    request = "Process lead L001 and prepare a personalized follow-up."
    plan = await sales.plan(request, task_id="task_sales_plan_1")

    assert plan.agent == "sales"
    assert len(plan.steps) == 4

    tool_sequence = [s.tool_id for s in plan.steps]
    assert tool_sequence == [
        "lookup_lead",
        "n8n_process_lead",
        "update_lead",
        "create_activity",
    ]


@pytest.mark.asyncio
async def test_sales_agent_plans_high_risk_followup_dispatch():
    """Verify Sales Agent sets up n8n_send_followup with approval required metadata."""
    sales = SalesAgent()
    request = "Send approved follow-up email to lead L001."
    plan = await sales.plan(request, task_id="task_sales_plan_2")

    assert plan.agent == "sales"
    assert plan.primary_tool == "n8n_send_followup"
    tool_sequence = [s.tool_id for s in plan.steps]
    assert "n8n_send_followup" in tool_sequence


# ==============================================================
# 4. End-to-End Workflow Execution & Verification Tests
# ==============================================================

@pytest.mark.asyncio
async def test_lead_processing_workflow_execution():
    """Verify end-to-end execution of lead processing with n8n tool, CRM update, and verification."""
    engine = TaskExecutionEngine()
    sales = SalesAgent()
    ds = get_data_service()

    task = Task(
        task_id="task_exec_process_lead",
        user_request="Process lead L001 and prepare a personalized follow-up.",
        selected_agent=AgentType.SALES,
        status=TaskStatus.CREATED,
    )

    plan = await sales.plan(task.user_request, task_id=task.task_id)

    # Mock n8n HTTP call
    mock_n8n_result = {
        "success": True,
        "workflow": "sales_process_lead",
        "task_id": task.task_id,
        "lead_id": "LEAD-001",
        "lead_status": "qualified",
        "qualification": {
            "score": 88,
            "tier": "TIER_1_ENTERPRISE",
            "status": "qualified",
            "rationale": "High-value enterprise prospect with 500+ seat potential",
        },
        "actions": [
            "Lead context retrieved",
            "Lead qualified as TIER_1_ENTERPRISE",
            "Personalized outreach proposal prepared",
        ],
        "follow_up": {
            "prepared": True,
            "recipient_name": "Rajesh Khanna",
            "recipient_email": "rajesh@cyberdyne.co.in",
            "subject": "Tailored Enterprise Solution for Cyberdyne Tech",
            "message": "Hello Rajesh Khanna, commercial proposal ready...",
        },
        "timestamp": "2026-09-18T12:00:00Z",
    }

    with patch("httpx.AsyncClient.post") as mock_post:
        mock_post.return_value = httpx.Response(200, json=mock_n8n_result)

        executed = await engine.execute_task(task, sales, plan)

        assert executed.status == TaskStatus.COMPLETED
        assert executed.result is not None
        assert executed.result["verification"]["verified"] is True

        # Verify CRM record was updated
        lead = await ds.get_lead("LEAD-001")
        assert lead is not None
        assert lead.status == "qualified"


@pytest.mark.asyncio
async def test_followup_dispatch_approval_gate_and_execution():
    """Verify that sending follow-up halts at WAITING_FOR_APPROVAL, then executes on approval."""
    from app.services.task_store import get_task_store
    engine = TaskExecutionEngine()
    sales = SalesAgent()
    task_store = get_task_store()

    task = Task(
        task_id="task_approval_followup",
        user_request="Send approved follow-up email to lead L001",
        selected_agent=AgentType.SALES,
        status=TaskStatus.CREATED,
    )

    plan = await sales.plan(task.user_request, task_id=task.task_id)
    await task_store.save_task(task)

    # 1. First execution should pause before the high-risk n8n_send_followup action
    executed = await engine.execute_task(task, sales, plan)

    assert executed.status == TaskStatus.WAITING_FOR_APPROVAL
    assert executed.result is not None
    assert executed.result["risk_level"] == "HIGH"
    assert task.current_approval_id is not None

    approval_id = task.current_approval_id

    # 2. Mock n8n delivery and grant human approval
    mock_delivery_result = {
        "success": True,
        "workflow": "sales_send_followup",
        "task_id": task.task_id,
        "lead_id": "LEAD-001",
        "delivery_info": {
            "delivery_id": "MSG-778899",
            "channel": "email",
            "status": "delivered",
            "recipient_name": "Rajesh Khanna",
            "recipient_email": "rajesh@cyberdyne.co.in",
            "subject": "Cyberdyne Proposal",
            "delivered_at": "2026-09-18T12:05:00Z",
        },
        "actions": [
            "Human approval verified",
            "Communication dispatched",
            "Delivery receipt logged",
        ],
    }

    with patch("httpx.AsyncClient.post") as mock_post:
        mock_post.return_value = httpx.Response(200, json=mock_delivery_result)

        # Approve and resume
        approved_task = await engine.resume_task_after_approval(
            approval_id=approval_id,
            resolved_by="sales_vp",
        )

        assert approved_task.status == TaskStatus.COMPLETED
        assert approved_task.result["verification"]["verified"] is True
        assert "n8n" in str(approved_task.result).lower() or "delivered" in str(approved_task.result).lower()


@pytest.mark.asyncio
async def test_followup_dispatch_rejection_flow():
    """Verify that rejecting follow-up aborts execution and marks task REJECTED / FAILED."""
    from app.services.task_store import get_task_store
    engine = TaskExecutionEngine()
    sales = SalesAgent()
    task_store = get_task_store()

    task = Task(
        task_id="task_reject_followup",
        user_request="Send approved follow-up email to lead L001",
        selected_agent=AgentType.SALES,
        status=TaskStatus.CREATED,
    )

    plan = await sales.plan(task.user_request, task_id=task.task_id)
    await task_store.save_task(task)

    # 1. Execution halts at WAITING_FOR_APPROVAL
    executed = await engine.execute_task(task, sales, plan)
    assert executed.status == TaskStatus.WAITING_FOR_APPROVAL
    assert task.current_approval_id is not None
    approval_id = task.current_approval_id

    # 2. Reject the action
    stopped_task = await engine.stop_task_after_rejection(
        approval_id=approval_id,
        rejection_reason="Pricing discount must be renegotiated first",
        resolved_by="sales_vp",
    )

    assert stopped_task.status == TaskStatus.FAILED
    if stopped_task.verification_result:
        assert stopped_task.verification_result.get("verified") is False
    if stopped_task.verification_result:
        assert stopped_task.verification_result.get("verified") is False


# ==============================================================
# 5. Integration Status API Test
# ==============================================================

def test_get_n8n_status_api():
    """Verify GET /api/v1/integrations/n8n/status returns live integration health."""
    resp = client.get("/api/v1/integrations/n8n/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "configured" in data
    assert data["configured"] is True
    assert "registered_workflows" in data
    assert "sales_process_lead" in data["registered_workflows"]
    assert "sales_send_followup" in data["registered_workflows"]


# ==============================================================
# 6. Live Local Integration Test (Against Local n8n Docker)
# ==============================================================

@pytest.mark.asyncio
async def test_live_local_n8n_docker_integration():
    """LIVE integration test confirming AgentX connects to the real local n8n Docker instance."""
    provider = N8nToolProvider()
    health = await provider.check_health()

    if not health.get("available"):
        pytest.skip(f"Local n8n Docker instance is offline: {health.get('error')}")

    # Invoke real workflow on local container
    payload = N8nInvocationPayload(
        task_id="test_live_docker_run",
        agent_id="sales",
        workflow_id="sales_process_lead",
        lead_id="LEAD-001",
        requested_action="process_lead",
        context={
            "name": "Rajesh Khanna",
            "company": "Cyberdyne Tech",
            "source": "inbound_enterprise",
            "notes": "Inquired about 500 seat enterprise expansion",
        },
    )

    result = await provider.invoke_workflow(payload)
    assert result.success is True
    assert result.workflow == "sales_process_lead"
    assert result.lead_status == "qualified"
    assert result.qualification is not None
    assert result.qualification.get("tier") == "TIER_1_ENTERPRISE"
    assert result.follow_up is not None
    assert result.follow_up.get("prepared") is True
