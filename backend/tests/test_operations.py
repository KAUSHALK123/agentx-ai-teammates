"""Tests for Phase 9 — Operations Teammate + Real n8n Workflow Integration."""

import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
import httpx
import pytest

from app.agents.operations_agent import OperationsAgent
from app.agents.router import AgentRouter
from app.models.approval import RiskLevel
from app.models.n8n import (
    APPROVED_N8N_WORKFLOWS,
    N8nExecutionResult,
    N8nInvocationPayload,
    get_n8n_workflow_definition,
)
from app.models.plan import StructuredTaskPlan
from app.models.task import AgentType, Task, TaskStatus
from app.services.approval_policy import ApprovalPolicyService
from app.services.data_service import get_data_service
from app.services.execution_engine import TaskExecutionEngine
from app.services.n8n_provider import N8nToolProvider, get_n8n_provider
from app.tools.n8n_tools import N8nOperationsDailyCheckTool


# ==============================================================
# 1. Operations Teammate Capabilities & Routing
# ==============================================================

def test_operations_agent_capabilities():
    """Verify Operations Agent has registered operational capabilities and available tools."""
    ops = OperationsAgent()
    assert ops.agent_id == "operations"
    assert ops.agent_type == AgentType.OPERATIONS
    cap_names = [c.name for c in ops.capabilities]
    assert "analyze_business_data" in cap_names
    assert "generate_report" in cap_names
    assert "verify_records" in cap_names
    assert "identify_exception" in cap_names
    assert "prepare_operational_action" in cap_names

    assert "n8n_operations_check" in ops.available_tools
    assert "get_business_data" in ops.available_tools
    assert "verify_record" in ops.available_tools
    assert "create_activity" in ops.available_tools


@pytest.mark.asyncio
async def test_operations_request_routing():
    """Verify router directs operational, inventory, and business check requests to Operations."""
    router = AgentRouter()

    requests = [
        "Run today's operations check and tell me what needs attention.",
        "Process the daily operations workflow.",
        "Check warehouse inventory anomalies and generate daily report.",
        "Find records that need follow-up.",
    ]

    for req in requests:
        route_res = await router.determine_route(req)
        assert route_res.selected_agent == AgentType.OPERATIONS, f"Failed for request: {req}"


# ==============================================================
# 2. Planning & Adaptive Decision Making
# ==============================================================

@pytest.mark.asyncio
async def test_operations_agent_plans_n8n_workflow():
    """Verify Operations Agent plans n8n workflow for daily check and report requests."""
    ops = OperationsAgent()
    request = "Run today's operations check and tell me what needs attention."
    plan = await ops.plan(request, task_id="task_ops_plan_1")

    assert plan.agent == "operations"
    assert plan.primary_tool == "n8n_operations_check"
    tool_sequence = [s.tool_id for s in plan.steps]
    assert tool_sequence == ["get_business_data", "n8n_operations_check", "create_activity"]


@pytest.mark.asyncio
async def test_operations_agent_plans_standard_record_audit():
    """Verify Operations Agent uses standard inspection tools when reviewing specific records."""
    ops = OperationsAgent()
    request = "Check today's business data and verify today's business records."
    plan = await ops.plan(request, task_id="task_ops_plan_2")

    assert plan.agent == "operations"
    assert plan.primary_tool == "get_business_data"
    tool_sequence = [s.tool_id for s in plan.steps]
    assert tool_sequence == ["get_business_data", "verify_record", "create_activity"]


@pytest.mark.asyncio
async def test_operations_agent_plans_high_risk_deletion():
    """Verify destructive data operations plan delete_record tool."""
    ops = OperationsAgent()
    request = "Purge and delete outdated transaction records from warehouse audit."
    plan = await ops.plan(request, task_id="task_ops_plan_3")

    assert plan.agent == "operations"
    assert plan.primary_tool == "delete_record"
    tool_sequence = [s.tool_id for s in plan.steps]
    assert "delete_record" in tool_sequence


# ==============================================================
# 3. Registry & Tool Provider Tests
# ==============================================================

def test_operations_n8n_registry_entry():
    """Verify operations_daily_business_check definition in registry."""
    wf_def = get_n8n_workflow_definition("operations_daily_business_check")
    assert wf_def is not None
    assert wf_def.workflow_id == "operations_daily_business_check"
    assert wf_def.allowed_agent == "operations"
    assert wf_def.risk_level == "LOW"
    assert wf_def.webhook_path == "agentx-operations-daily-check"


@pytest.mark.asyncio
async def test_n8n_provider_unauthorized_agent_rejection():
    """Verify Sales Agent is rejected if attempting to invoke the Operations workflow."""
    provider = N8nToolProvider(base_url="http://mock-n8n:5678")
    payload = N8nInvocationPayload(
        task_id="task_unauth",
        agent_id="sales",
        workflow_id="operations_daily_business_check",
        requested_action="daily_business_check",
    )
    res = await provider.invoke_workflow(payload)
    assert res.success is False
    assert "unauthorized" in (res.error or "").lower()


@pytest.mark.asyncio
async def test_n8n_operations_tool_mock_success():
    """Verify N8nOperationsDailyCheckTool processes n8n response and creates activity records."""
    tool = N8nOperationsDailyCheckTool()
    ds = get_data_service()

    mock_response = {
        "success": True,
        "workflow": "operations_daily_business_check",
        "task_id": "task_ops_tool_test",
        "records_processed": 25,
        "exceptions_found": 4,
        "requires_attention": True,
        "metrics": {
            "successful": 21,
            "failed": 2,
            "pending": 2,
            "total": 25,
            "exception_rate": 0.16,
        },
        "actions": [
            "Business data processed",
            "Exceptions identified",
            "Follow-up activities created",
        ],
        "report": {
            "summary": "Daily operations check completed. 25 records processed. 4 exceptions detected.",
            "priority_items": [
                {"item_id": "TXN-9002", "severity": "HIGH", "issue": "Payment gateway timeout"},
                {"item_id": "ORD-1003", "severity": "HIGH", "issue": "Order unresolved beyond 48 hours"},
            ],
            "created_activities": [
                {"activity_id": "ACT-OP-101", "type": "payment_investigation", "target": "TXN-9002"},
                {"activity_id": "ACT-OP-102", "type": "fulfillment_expedite", "target": "ORD-1003"},
            ],
        },
        "timestamp": "2026-09-18T14:00:00Z",
    }

    with patch("httpx.AsyncClient.post") as mock_post:
        mock_post.return_value = httpx.Response(200, json=mock_response)

        result = await tool.execute(task_id="task_ops_tool_test", category="daily_audit")

        assert result.success is True
        assert result.data["records_processed"] == 25
        assert result.data["exceptions_found"] == 4
        assert result.data["requires_attention"] is True
        assert "4 exceptions detected" in result.message

        # Check synchronized activities in DataService
        activities = await ds.get_activities_for_task("task_ops_tool_test")
        assert len(activities) >= 2
        act_types = [a.type for a in activities]
        assert "payment_investigation" in act_types
        assert "fulfillment_expedite" in act_types


@pytest.mark.asyncio
async def test_n8n_operations_tool_idempotency():
    """Verify identical operational audit requests return cached execution without duplicate network hits."""
    provider = N8nToolProvider(base_url="http://mock-n8n:5678")
    payload = N8nInvocationPayload(
        task_id="task_ops_idempotent",
        agent_id="operations",
        workflow_id="operations_daily_business_check",
        requested_action="daily_business_check",
    )

    mock_resp = {
        "success": True,
        "workflow": "operations_daily_business_check",
        "records_processed": 25,
        "exceptions_found": 4,
        "requires_attention": True,
        "metrics": {"successful": 21, "failed": 2, "pending": 2},
    }

    with patch("httpx.AsyncClient.post") as mock_post:
        mock_post.return_value = httpx.Response(200, json=mock_resp)

        res1 = await provider.invoke_workflow(payload)
        assert res1.success is True
        assert mock_post.call_count == 1

        res2 = await provider.invoke_workflow(payload)
        assert res2.success is True
        assert mock_post.call_count == 1  # Served from cache


@pytest.mark.asyncio
async def test_n8n_operations_failure_handling():
    """Verify clear error codes on network failure, timeout, and malformed response."""
    provider = N8nToolProvider(base_url="http://invalid-n8n-host:9999", retry_attempts=0)

    # 1. Connection unavailable
    payload = N8nInvocationPayload(
        task_id="task_fail_1",
        agent_id="operations",
        workflow_id="operations_daily_business_check",
        requested_action="daily_business_check",
    )
    with patch("httpx.AsyncClient.post", side_effect=httpx.ConnectError("Connection refused")):
        res = await provider.invoke_workflow(payload)
        assert res.success is False
        assert "N8N_UNAVAILABLE" in (res.error or "")

    # 2. Timeout
    with patch("httpx.AsyncClient.post", side_effect=httpx.TimeoutException("Read timeout")):
        res = await provider.invoke_workflow(payload)
        assert res.success is False
        assert "N8N_TIMEOUT" in (res.error or "")

    # 3. Malformed JSON
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_post.return_value = httpx.Response(200, content=b"{not-valid-json}")
        res = await provider.invoke_workflow(payload)
        assert res.success is False
        assert "N8N_MALFORMED_RESPONSE" in (res.error or "")


# ==============================================================
# 4. End-to-End Task Execution & Verification
# ==============================================================

@pytest.mark.asyncio
async def test_operations_daily_check_execution_and_verification():
    """Verify end-to-end execution of operations daily check with verification engine."""
    engine = TaskExecutionEngine()
    ops = OperationsAgent()

    task = Task(
        task_id="task_exec_ops_check",
        user_request="Run today's operations check and tell me what needs attention.",
        selected_agent=AgentType.OPERATIONS,
        status=TaskStatus.CREATED,
    )

    plan = await ops.plan(task.user_request, task_id=task.task_id)

    mock_n8n_result = {
        "success": True,
        "workflow": "operations_daily_business_check",
        "task_id": task.task_id,
        "records_processed": 25,
        "exceptions_found": 4,
        "requires_attention": True,
        "metrics": {
            "successful": 21,
            "failed": 2,
            "pending": 2,
            "total": 25,
            "exception_rate": 0.16,
        },
        "actions": [
            "Business data processed",
            "Exceptions identified",
            "Follow-up activities created",
        ],
        "report": {
            "summary": "Daily operations check completed. 25 records processed. 4 exceptions detected.",
            "priority_items": [
                {"item_id": "TXN-9002", "severity": "HIGH", "issue": "Payment gateway timeout"},
            ],
            "created_activities": [
                {"activity_id": "ACT-OP-101", "type": "payment_investigation", "target": "TXN-9002"},
            ],
        },
        "timestamp": "2026-09-18T14:05:00Z",
    }

    with patch("httpx.AsyncClient.post") as mock_post:
        mock_post.return_value = httpx.Response(200, json=mock_n8n_result)

        executed = await engine.execute_task(task, ops, plan)

        assert executed.status == TaskStatus.COMPLETED
        assert executed.result is not None
        assert executed.result["verification"]["verified"] is True
        assert executed.result["verification"]["verification_type"] == "n8n_operations_audit"


# ==============================================================
# 5. Human Approval Gating for Risky Operations
# ==============================================================

@pytest.mark.asyncio
async def test_high_risk_operational_action_approval_gate():
    """Verify that destructive operations (e.g. data purge) halt for human approval."""
    policy = ApprovalPolicyService()
    decision = policy.evaluate(
        agent_id="operations",
        tool_id="delete_record",
        action="Delete outdated transaction logs from database",
        parameters={"table": "transactions", "cutoff": "2025-01-01"},
    )
    assert decision.approval_required is True
    assert decision.risk_level == RiskLevel.HIGH


# ==============================================================
# 6. Live Local n8n Docker Integration Test
# ==============================================================

@pytest.mark.asyncio
async def test_live_local_n8n_docker_operations_integration():
    """Real integration test against the running local n8n Docker instance."""
    provider = get_n8n_provider()

    # Verify n8n health
    health = await provider.check_health()
    if not health.get("available"):
        pytest.skip(f"Local n8n instance not reachable: {health.get('error')}")

    payload = N8nInvocationPayload(
        task_id=f"live-ops-task-{int(datetime.now(timezone.utc).timestamp())}",
        agent_id="operations",
        workflow_id="operations_daily_business_check",
        requested_action="daily_business_check",
        context={"audit_type": "live_integration_test"},
    )

    result = await provider.invoke_workflow(payload)

    if not result.success and "404" in str(result.error):
        pytest.skip(f"Operations webhook not active in local n8n container: {result.error}")

    assert result.success is True
    assert result.workflow in ("operations_daily_business_check", "03_operations_daily_check", "operations")
    assert result.metrics is not None or result.records_processed is not None
