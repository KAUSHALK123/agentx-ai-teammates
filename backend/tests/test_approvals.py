import pytest
from fastapi.testclient import TestClient

from app.agents.operations_agent import OperationsAgent
from app.agents.sales_agent import SalesAgent
from app.agents.support_agent import SupportAgent
from app.main import app
from app.models.approval import ApprovalRecord, ApprovalStatus, RiskLevel
from app.models.plan import PlanStep, StepStatus, StructuredTaskPlan
from app.models.task import AgentType, Task, TaskStatus
from app.services.approval_policy import ApprovalPolicyService, get_approval_policy
from app.services.approval_store import InMemoryApprovalStore, get_approval_store
from app.services.execution_engine import ExecutionContext, TaskExecutionEngine, get_execution_engine
from app.services.orchestrator import get_orchestrator
from app.services.task_store import get_task_store
from app.services.tool_executor import get_tool_executor


@pytest.fixture
def client():
    return TestClient(app)


# ==============================================================
# 1. Approval Policy & Risk Classification Tests
# ==============================================================

def test_risk_classification_low_risk():
    """Verify read/lookup/report actions are classified as LOW_RISK without approval."""
    policy = ApprovalPolicyService()

    # Read/lookup
    dec1 = policy.evaluate_action(
        agent="support",
        tool_id="lookup_customer",
        action="Lookup customer profile",
        proposed_input={"customer_id": "CUST-001"},
    )
    assert dec1.risk_level == RiskLevel.LOW
    assert dec1.approval_required is False

    # Search
    dec2 = policy.evaluate_action(
        agent="sales",
        tool_id="search_catalog",
        action="Search product catalog",
        proposed_input={"query": "starter kit"},
    )
    assert dec2.risk_level == RiskLevel.LOW
    assert dec2.approval_required is False

    # Internal activity logging
    dec3 = policy.evaluate_action(
        agent="operations",
        tool_id="create_activity",
        action="Log internal operational status check",
        proposed_input={"type": "STATUS_CHECK", "message": "System healthy"},
    )
    assert dec3.risk_level == RiskLevel.LOW
    assert dec3.approval_required is False


def test_risk_classification_high_risk():
    """Verify external emails, refunds, financial actions, and cancellations are HIGH_RISK."""
    policy = ApprovalPolicyService()

    # External email / communication
    dec1 = policy.evaluate_action(
        agent="support",
        tool_id="create_activity",
        action="Send customer response email to external client",
        proposed_input={"type": "EMAIL_SENT", "message": "Here is your refund confirmation"},
    )
    assert dec1.risk_level == RiskLevel.HIGH
    assert dec1.approval_required is True
    assert "External" in dec1.reason or "supervisor" in dec1.reason

    # Refund / financial action
    dec2 = policy.evaluate_action(
        agent="support",
        tool_id="create_activity",
        action="Process refund compensation of 1500 INR",
        proposed_input={"type": "REFUND", "amount": 1500},
    )
    assert dec2.risk_level == RiskLevel.HIGH
    assert dec2.approval_required is True
    assert "Financial" in dec2.reason or "refund" in dec2.reason.lower()

    # Deletion / cancellation
    dec3 = policy.evaluate_action(
        agent="operations",
        tool_id="create_activity",
        action="Cancel order and delete transaction record",
        proposed_input={"order_id": "ORD-999"},
    )
    assert dec3.risk_level == RiskLevel.HIGH
    assert dec3.approval_required is True


# ==============================================================
# 2. Execution Engine Pause & Approval Record Tests
# ==============================================================

@pytest.mark.asyncio
async def test_low_risk_action_executes_automatically():
    """Low-risk action executes completely without triggering WAITING_FOR_APPROVAL."""
    engine = TaskExecutionEngine()
    agent = SupportAgent()
    task = Task(
        task_id="test_task_low_risk",
        user_request="Find customer CUST-001",
        selected_agent=AgentType.SUPPORT,
        status=TaskStatus.CREATED,
    )
    plan = StructuredTaskPlan(
        task_id=task.task_id,
        agent="support",
        objective="Look up customer",
        steps=[
            PlanStep(
                step_id=1,
                action="Query customer profile database",
                type="tool_action",
                tool_id="lookup_customer",
                input={"customer_id": "CUST-001"},
            )
        ],
    )

    executed = await engine.execute_task(task, agent, plan)

    assert executed.status == TaskStatus.COMPLETED
    assert task.current_approval_id is None
    assert plan.steps[0].status == StepStatus.COMPLETED.value


@pytest.mark.asyncio
async def test_high_risk_action_pauses_for_approval():
    """High-risk action pauses task execution and sets task status to WAITING_FOR_APPROVAL."""
    approval_store = get_approval_store()
    task_store = get_task_store()
    engine = TaskExecutionEngine()
    agent = SupportAgent()

    task = Task(
        task_id="test_task_high_risk",
        user_request="Send refund confirmation email to customer",
        selected_agent=AgentType.SUPPORT,
        status=TaskStatus.CREATED,
    )
    plan = StructuredTaskPlan(
        task_id=task.task_id,
        agent="support",
        objective="Send external email",
        steps=[
            PlanStep(
                step_id=1,
                action="Lookup customer record",
                type="tool_action",
                tool_id="lookup_customer",
                input={"customer_id": "CUST-001"},
            ),
            PlanStep(
                step_id=2,
                action="Send external response email to customer with refund confirmation",
                type="tool_action",
                tool_id="create_activity",
                input={
                    "type": "EMAIL_SENT",
                    "subject": "Refund Processed",
                    "customer_id": "CUST-001",
                },
            ),
        ],
    )

    await task_store.save_task(task)
    executed = await engine.execute_task(task, agent, plan)

    # Step 1 should be completed, Step 2 should be WAITING_FOR_APPROVAL
    assert executed.status == TaskStatus.WAITING_FOR_APPROVAL
    assert task.current_approval_id is not None

    # Step 1 was executed
    assert plan.steps[0].status == StepStatus.COMPLETED.value
    # Step 2 was paused BEFORE execution
    assert plan.steps[1].status == StepStatus.PENDING.value
    assert "Waiting for human approval" in plan.steps[1].result_summary

    # Verify approval record
    record = await approval_store.get_approval(task.current_approval_id)
    assert record is not None
    assert record.task_id == task.task_id
    assert record.step_id == 2
    assert record.risk_level == RiskLevel.HIGH.value
    assert record.status == ApprovalStatus.PENDING.value
    assert record.tool_id == "create_activity"


# ==============================================================
# 3. Resume and Reject Tests
# ==============================================================

@pytest.mark.asyncio
async def test_approve_resumes_execution_and_verifies():
    """Approving a pending high-risk action executes it and finishes the task."""
    approval_store = get_approval_store()
    task_store = get_task_store()
    engine = TaskExecutionEngine()
    agent = SupportAgent()

    task = Task(
        task_id="test_task_approve_flow",
        user_request="Send compensation email",
        selected_agent=AgentType.SUPPORT,
        status=TaskStatus.CREATED,
    )
    plan = StructuredTaskPlan(
        task_id=task.task_id,
        agent="support",
        objective="Approve and finish",
        steps=[
            PlanStep(
                step_id=1,
                action="Send external communication email with compensation",
                type="tool_action",
                tool_id="create_activity",
                input={"type": "EMAIL_SENT", "message": "Compensation issued"},
            )
        ],
    )

    await task_store.save_task(task)

    # First run: pauses
    executed = await engine.execute_task(task, agent, plan)
    assert executed.status == TaskStatus.WAITING_FOR_APPROVAL
    approval_id = task.current_approval_id

    # Human approves
    resumed_task = await engine.resume_task_after_approval(
        approval_id=approval_id,
        resolved_by="human_manager_alice",
    )

    assert resumed_task.status == TaskStatus.COMPLETED
    assert resumed_task.current_approval_id is None
    assert resumed_task.plan.steps[0].status == StepStatus.COMPLETED.value


    # Record marked approved
    rec = await approval_store.get_approval(approval_id)
    assert rec.status == ApprovalStatus.APPROVED.value
    assert rec.resolved_by == "human_manager_alice"
    assert rec.resolved_at is not None


@pytest.mark.asyncio
async def test_reject_prevents_execution_and_fails_safely():
    """Rejecting a pending high-risk action does not run tool and terminates task."""
    approval_store = get_approval_store()
    task_store = get_task_store()
    engine = TaskExecutionEngine()
    agent = SupportAgent()

    task = Task(
        task_id="test_task_reject_flow",
        user_request="Delete customer history record",
        selected_agent=AgentType.SUPPORT,
        status=TaskStatus.CREATED,
    )
    plan = StructuredTaskPlan(
        task_id=task.task_id,
        agent="support",
        objective="Reject deletion",
        steps=[
            PlanStep(
                step_id=1,
                action="Delete customer activity history",
                type="tool_action",
                tool_id="create_activity",
                input={"type": "DELETE_RECORD", "id": "123"},
            )
        ],
    )

    await task_store.save_task(task)
    await engine.execute_task(task, agent, plan)

    assert task.status == TaskStatus.WAITING_FOR_APPROVAL
    approval_id = task.current_approval_id

    # Human rejects
    stopped_task = await engine.stop_task_after_rejection(
        approval_id=approval_id,
        rejection_reason="Unauthorized deletion request",
        resolved_by="security_admin",
    )

    assert stopped_task.status == TaskStatus.FAILED
    assert stopped_task.plan.steps[0].status == StepStatus.FAILED.value
    assert "Unauthorized deletion request" in stopped_task.plan.steps[0].result_summary

    rec = await approval_store.get_approval(approval_id)
    assert rec.status == ApprovalStatus.REJECTED.value
    assert rec.rejection_reason == "Unauthorized deletion request"
    assert rec.resolved_by == "security_admin"


# ==============================================================
# 4. Security & Edge Case Tests
# ==============================================================

@pytest.mark.asyncio
async def test_duplicate_approval_rejected():
    """Attempting to re-approve an already resolved approval raises ValueError."""
    task_store = get_task_store()
    engine = TaskExecutionEngine()

    task = Task(
        task_id="test_dup_task",
        user_request="Send email",
        selected_agent=AgentType.SUPPORT,
        status=TaskStatus.CREATED,
    )
    plan = StructuredTaskPlan(
        task_id=task.task_id,
        agent="support",
        objective="Test duplicate",
        steps=[
            PlanStep(
                step_id=1,
                action="Send external email notification",
                type="tool_action",
                tool_id="create_activity",
                input={"type": "EMAIL_SENT"},
            )
        ],
    )

    await task_store.save_task(task)
    await engine.execute_task(task, SupportAgent(), plan)
    approval_id = task.current_approval_id

    # Approve once
    await engine.resume_task_after_approval(approval_id, resolved_by="admin")

    # Second approve attempt must fail
    with pytest.raises(ValueError, match="already resolved"):
        await engine.resume_task_after_approval(approval_id, resolved_by="admin2")


@pytest.mark.asyncio
async def test_invalid_approval_id():
    """Non-existent approval ID raises ValueError in resume/stop."""
    engine = TaskExecutionEngine()
    with pytest.raises(ValueError, match="not found"):
        await engine.resume_task_after_approval("non_existent_appr_id")

    with pytest.raises(ValueError, match="not found"):
        await engine.stop_task_after_rejection("non_existent_appr_id", "some reason")


@pytest.mark.asyncio
async def test_approval_cannot_bypass_tool_permissions():
    """Even if approved, executing an unauthorized tool must be blocked by tool permissions."""
    engine = TaskExecutionEngine()
    sales = SalesAgent()  # Sales cannot execute lookup_customer

    task = Task(
        task_id="test_perm_bypass",
        user_request="Sales external refund",
        selected_agent=AgentType.SALES,
        status=TaskStatus.CREATED,
    )
    plan = StructuredTaskPlan(
        task_id=task.task_id,
        agent="sales",
        objective="Unauthorized tool test",
        steps=[
            PlanStep(
                step_id=1,
                action="Process external refund via unauthorized tool",
                type="tool_action",
                tool_id="lookup_order",  # Not in sales toolset!
                input={"order_id": "ORD-1001"},
            )

        ],
    )

    # Initial check will trigger approval because of 'refund'
    await get_task_store().save_task(task)
    await engine.execute_task(task, sales, plan)
    approval_id = task.current_approval_id
    assert approval_id is not None

    # Even after approval, tool execution must fail because of permission check
    resumed = await engine.resume_task_after_approval(approval_id)
    assert resumed.status == TaskStatus.FAILED
    assert "not authorized" in resumed.plan.steps[0].result_summary.lower()


# ==============================================================
# 5. REST API Endpoints Tests
# ==============================================================

def test_api_list_and_get_approvals(client):
    """Test GET /approvals and GET /approvals/{id}."""
    # Run a high-risk request through orchestrator
    req_payload = {
        "user_request": "Investigate customer C001 order ORD-1001 and send external email refund update",
        "selected_agent": "support",
    }
    r = client.post("/tasks", json=req_payload)
    assert r.status_code == 201
    task_data = r.json()
    task_id = task_data["task_id"]
    assert task_data["status"] == "WAITING_FOR_APPROVAL"

    # List pending approvals
    r_list = client.get("/approvals")
    assert r_list.status_code == 200
    approvals = r_list.json()
    assert len(approvals) > 0
    match = [a for a in approvals if a["task_id"] == task_id]
    assert len(match) == 1
    approval_id = match[0]["approval_id"]

    # Get single approval details
    r_single = client.get(f"/approvals/{approval_id}")
    assert r_single.status_code == 200
    detail = r_single.json()
    assert detail["approval_id"] == approval_id
    assert detail["risk_level"] == "HIGH"
    assert detail["status"] == "PENDING"


def test_api_approve_endpoint(client):
    """Test POST /approvals/{id}/approve resumes task to completion."""
    r = client.post("/tasks", json={
        "user_request": "Check customer C001 order ORD-1001 and send external email confirmation",
        "selected_agent": "support",
    })
    assert r.status_code == 201
    task_id = r.json()["task_id"]
    assert r.json()["status"] == "WAITING_FOR_APPROVAL"

    # Get pending approval
    r_list = client.get("/approvals")
    pending = [a for a in r_list.json() if a["task_id"] == task_id]
    assert len(pending) > 0
    appr_id = pending[0]["approval_id"]

    # Approve
    r_appr = client.post(f"/approvals/{appr_id}/approve", params={"resolved_by": "qa_tester"})
    assert r_appr.status_code == 200
    res_data = r_appr.json()
    assert res_data["status"] == "APPROVED"
    assert res_data["task_status"] == "COMPLETED"

    # Verify task state in GET /tasks/{id}/execution
    r_exec_hist = client.get(f"/tasks/{task_id}/execution")
    assert r_exec_hist.status_code == 200
    assert r_exec_hist.json()["task_status"] == "COMPLETED"


def test_api_reject_endpoint(client):
    """Test POST /approvals/{id}/reject stops task."""
    r = client.post("/tasks", json={
        "user_request": "Check customer C001 order ORD-1001 and send external email message",
        "selected_agent": "support",
    })
    assert r.status_code == 201
    task_id = r.json()["task_id"]
    assert r.json()["status"] == "WAITING_FOR_APPROVAL"


    r_list = client.get("/approvals")
    pending = [a for a in r_list.json() if a["task_id"] == task_id]
    assert len(pending) > 0
    appr_id = pending[0]["approval_id"]

    # Reject
    r_rej = client.post(f"/approvals/{appr_id}/reject", json={"reason": "Disallowed payment action"})
    assert r_rej.status_code == 200
    res_data = r_rej.json()
    assert res_data["status"] == "REJECTED"
    assert res_data["task_status"] == "FAILED"

    # Check 400 when attempting to reject again
    r_rej_again = client.post(f"/approvals/{appr_id}/reject", json={"reason": "Again"})
    assert r_rej_again.status_code == 400
