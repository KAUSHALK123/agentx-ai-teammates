import pytest
from fastapi.testclient import TestClient

from app.agents.operations_agent import OperationsAgent
from app.agents.sales_agent import SalesAgent
from app.agents.support_agent import SupportAgent
from app.main import app
from app.models.plan import PlanStep, StepStatus, StructuredTaskPlan
from app.models.task import AgentType, Task, TaskStatus
from app.services.data_service import get_data_service
from app.services.execution_engine import ExecutionContext, TaskExecutionEngine, get_execution_engine
from app.services.orchestrator import get_orchestrator
from app.services.task_store import get_task_store
from app.services.tool_executor import get_tool_executor
from app.services.verifier import TaskVerifier


@pytest.fixture
def client():
    return TestClient(app)


# ==============================================================
# 1. Core Execution Engine Tests
# ==============================================================

@pytest.mark.asyncio
async def test_task_execution_single_step():
    """Verify single-step plan execution through TaskExecutionEngine."""
    engine = TaskExecutionEngine()
    support = SupportAgent()
    task = Task(
        task_id="test_task_single",
        user_request="Lookup customer CUST-001",
        selected_agent=AgentType.SUPPORT,
        status=TaskStatus.CREATED,
    )
    plan = StructuredTaskPlan(
        task_id=task.task_id,
        agent="support",
        objective="Look up single customer",
        steps=[
            PlanStep(
                step_id=1,
                action="Find customer profile in system",
                type="tool_action",
                tool_id="lookup_customer",
                input={"customer_id": "CUST-001"},
            )
        ],
    )

    executed = await engine.execute_task(task, support, plan)

    assert executed.status == TaskStatus.COMPLETED
    assert len(plan.steps) == 1
    assert plan.steps[0].status == StepStatus.COMPLETED.value
    assert plan.steps[0].started_at is not None
    assert plan.steps[0].completed_at is not None
    assert "Alice Sharma" in (plan.steps[0].result_summary or "")
    assert len(executed.execution_records) == 1
    assert executed.result is not None
    assert executed.result["verification"]["verified"] is True


@pytest.mark.asyncio
async def test_variable_propagation_across_steps():
    """Verify variables (e.g. customer_id) propagate from earlier steps to later steps."""
    engine = TaskExecutionEngine()
    support = SupportAgent()
    task = Task(
        task_id="test_task_propagate",
        user_request="Investigate customer C001",
        selected_agent=AgentType.SUPPORT,
        status=TaskStatus.CREATED,
    )
    plan = StructuredTaskPlan(
        task_id=task.task_id,
        agent="support",
        objective="Find customer and their orders",
        steps=[
            PlanStep(
                step_id=1,
                action="Find customer profile",
                type="tool_action",
                tool_id="lookup_customer",
                input={"customer_id": "CUST-001"},
            ),
            PlanStep(
                step_id=2,
                action="Lookup orders using discovered customer_id",
                type="tool_action",
                tool_id="lookup_order",
                # No input provided: must safely consume customer_id propagated from step 1
            ),
        ],
    )

    executed = await engine.execute_task(task, support, plan)

    assert executed.status == TaskStatus.COMPLETED
    assert plan.steps[0].status == StepStatus.COMPLETED.value
    assert plan.steps[1].status == StepStatus.COMPLETED.value
    assert len(executed.execution_records) == 2
    assert "CUST-001" in str(executed.execution_records[1]["result_summary"])


@pytest.mark.asyncio
async def test_step_and_task_status_transitions():
    """Verify status transitions from PENDING -> RUNNING -> COMPLETED."""
    engine = TaskExecutionEngine()
    support = SupportAgent()
    task = Task(
        task_id="test_task_transitions",
        user_request="Check business data",
        selected_agent=AgentType.SUPPORT,
        status=TaskStatus.CREATED,
    )
    plan = StructuredTaskPlan(
        task_id=task.task_id,
        agent="support",
        objective="Execute step transitions",
        steps=[
            PlanStep(
                step_id=1,
                action="Lookup customer CUST-002",
                type="tool_action",
                tool_id="lookup_customer",
                input={"customer_id": "CUST-002"},
            )
        ],
    )

    assert plan.steps[0].status == StepStatus.PENDING.value
    executed = await engine.execute_task(task, support, plan)
    assert plan.steps[0].status == StepStatus.COMPLETED.value
    assert executed.status == TaskStatus.COMPLETED


# ==============================================================
# 2. Write Verification Tests
# ==============================================================

@pytest.mark.asyncio
async def test_write_verification_success_lead_update():
    """Verify that update_lead is confirmed by real secondary data store inspection."""
    engine = TaskExecutionEngine()
    sales = SalesAgent()
    ds = get_data_service()

    task = Task(
        task_id="test_lead_verify_success",
        user_request="Update lead LEAD-101 status to contacted",
        selected_agent=AgentType.SALES,
        status=TaskStatus.CREATED,
    )
    plan = StructuredTaskPlan(
        task_id=task.task_id,
        agent="sales",
        objective="Update lead status with verification",
        steps=[
            PlanStep(
                step_id=1,
                action="Update lead status in CRM",
                type="tool_action",
                tool_id="update_lead",
                input={"lead_id": "LEAD-101", "status": "contacted", "notes": "Contacted by sales"},
            )
        ],
    )

    executed = await engine.execute_task(task, sales, plan)

    assert executed.status == TaskStatus.COMPLETED
    assert executed.result["verification"]["verified"] is True
    # Confirm in data service directly
    lead = await ds.get_lead("LEAD-101")
    assert lead is not None
    assert lead.status == "contacted"


@pytest.mark.asyncio
async def test_write_verification_failure():
    """Verify that a corrupted or mismatched write state causes verification to fail the task."""
    ds = get_data_service()
    task = Task(
        task_id="test_lead_verify_fail",
        user_request="Test verification failure",
        selected_agent=AgentType.SALES,
        status=TaskStatus.CREATED,
    )

    # Simulated tool result with mismatched expected state
    fake_tool_result = {
        "success": True,
        "tool_id": "update_lead",
        "data": {
            "lead_id": "LEAD-999",  # Non-existent lead
            "status": "qualified",
        },
        "error": None,
    }

    verification = await TaskVerifier.verify_task_execution(
        task=task,
        completed_tool_results=[fake_tool_result],
        data_service=ds,
    )

    assert verification.verified is False
    assert verification.recommended_status == TaskStatus.FAILED
    assert "not found" in verification.summary


# ==============================================================
# 3. Security, Failure & Retry Tests
# ==============================================================

@pytest.mark.asyncio
async def test_unauthorized_tool_execution_stops_task():
    """Verify that attempting to execute an unauthorized tool fails the step and stops execution."""
    engine = TaskExecutionEngine()
    support = SupportAgent()  # Support has no update_lead permission

    task = Task(
        task_id="test_unauth_task",
        user_request="Support agent trying to update lead",
        selected_agent=AgentType.SUPPORT,
        status=TaskStatus.CREATED,
    )
    plan = StructuredTaskPlan(
        task_id=task.task_id,
        agent="support",
        objective="Attempt unauthorized tool",
        steps=[
            PlanStep(
                step_id=1,
                action="Attempt unauthorized lead update",
                type="tool_action",
                tool_id="update_lead",
                input={"lead_id": "LEAD-101", "status": "qualified"},
            ),
            PlanStep(
                step_id=2,
                action="Subsequent action that must be skipped",
                type="tool_action",
                tool_id="lookup_customer",
                input={"customer_id": "CUST-001"},
            ),
        ],
    )

    executed = await engine.execute_task(task, support, plan)

    assert executed.status == TaskStatus.FAILED
    assert plan.steps[0].status == StepStatus.FAILED.value
    assert "not authorized" in str(plan.steps[0].error).lower()
    # Step 2 must have been skipped
    assert plan.steps[1].status == StepStatus.SKIPPED.value


@pytest.mark.asyncio
async def test_tool_failure_handling():
    """Verify that tool failure is captured, marks step FAILED, and prevents subsequent execution."""
    engine = TaskExecutionEngine()
    support = SupportAgent()

    task = Task(
        task_id="test_tool_fail_task",
        user_request="Lookup non-existent customer",
        selected_agent=AgentType.SUPPORT,
        status=TaskStatus.CREATED,
    )
    plan = StructuredTaskPlan(
        task_id=task.task_id,
        agent="support",
        objective="Test tool failure",
        steps=[
            PlanStep(
                step_id=1,
                action="Lookup non-existent customer ID",
                type="tool_action",
                tool_id="lookup_customer",
                input={"customer_id": "NON_EXISTENT_CUST_999"},
            ),
            PlanStep(
                step_id=2,
                action="Dependent order lookup",
                type="tool_action",
                tool_id="lookup_order",
            ),
        ],
    )

    executed = await engine.execute_task(task, support, plan)

    assert executed.status == TaskStatus.FAILED
    assert plan.steps[0].status == StepStatus.FAILED.value
    assert plan.steps[1].status == StepStatus.SKIPPED.value
    assert executed.result["verification"]["verified"] is False


# ==============================================================
# 4. Mandatory Demo Flows (Support, Sales, Operations)
# ==============================================================

@pytest.mark.asyncio
async def test_demo_flow_1_support():
    """FLOW 1 — SUPPORT: 'Investigate customer C001's order.'
    Executes: lookup_customer -> lookup_order -> lookup_transaction -> verify -> complete.
    """
    orchestrator = get_orchestrator()
    task = await orchestrator.create_and_run_task("Investigate customer C001's order.")

    assert task.status == TaskStatus.COMPLETED
    assert task.selected_agent == AgentType.SUPPORT
    assert task.plan is not None
    assert len(task.plan.steps) >= 3

    # Confirm step tools were executed
    executed_tools = [r["tool_id"] for r in task.execution_records]
    assert "lookup_customer" in executed_tools
    assert "lookup_order" in executed_tools
    assert "lookup_transaction" in executed_tools

    # Confirm verification
    assert task.result["verification"]["verified"] is True
    assert len(task.result["actions_performed"]) >= 3


@pytest.mark.asyncio
async def test_demo_flow_2_sales():
    """FLOW 2 — SALES: 'Process lead L001 and update the lead status.'
    Executes: lookup_lead -> analyze -> update_lead -> verify -> create_activity -> complete.
    """
    orchestrator = get_orchestrator()
    task = await orchestrator.create_and_run_task("Process lead L001 and update the lead status.")

    assert task.status == TaskStatus.COMPLETED
    assert task.selected_agent == AgentType.SALES
    assert task.plan is not None

    executed_tools = [r["tool_id"] for r in task.execution_records]
    assert "lookup_lead" in executed_tools
    assert "update_lead" in executed_tools
    assert "create_activity" in executed_tools

    assert task.result["verification"]["verified"] is True
    assert task.result["verification"]["verification_type"] == "record_match"


@pytest.mark.asyncio
async def test_demo_flow_3_operations():
    """FLOW 3 — OPERATIONS: 'Check today's business data and identify anything requiring attention.'
    Executes: get_business_data -> analyze -> verify_record -> create_activity -> complete.
    """
    orchestrator = get_orchestrator()
    task = await orchestrator.create_and_run_task(
        "Check today's business data and identify anything requiring attention."
    )

    assert task.status in [TaskStatus.COMPLETED, TaskStatus.ESCALATED]
    assert task.selected_agent == AgentType.OPERATIONS
    assert task.plan is not None

    executed_tools = [r["tool_id"] for r in task.execution_records]
    assert "get_business_data" in executed_tools
    assert "verify_record" in executed_tools
    assert "create_activity" in executed_tools

    assert task.result["verification"]["verified"] is True


# ==============================================================
# 5. API Endpoints Tests
# ==============================================================

def test_api_execute_task_flow(client: TestClient):
    """Test POST /tasks/plan -> POST /tasks/{task_id}/execute -> GET /tasks/{task_id}/execution."""
    # 1. Create a plan
    plan_resp = client.post("/tasks/plan", json={"user_request": "Investigate customer C001's order."})
    assert plan_resp.status_code == 200
    plan_data = plan_resp.json()
    task_id = plan_data["task_id"]
    assert task_id is not None

    # 2. Execute the task
    exec_resp = client.post(f"/tasks/{task_id}/execute")
    assert exec_resp.status_code == 200
    exec_data = exec_resp.json()
    assert exec_data["task_id"] == task_id
    assert exec_data["status"] == "COMPLETED"
    assert exec_data["selected_agent"] == "support"
    assert exec_data["final_result"] is not None

    # 3. Retrieve execution details
    trace_resp = client.get(f"/tasks/{task_id}/execution")
    assert trace_resp.status_code == 200
    trace_data = trace_resp.json()
    assert trace_data["task_id"] == task_id
    assert trace_data["task_status"] == "COMPLETED"
    assert trace_data["selected_agent"] == "support"
    assert len(trace_data["steps"]) >= 3
    assert len(trace_data["execution_records"]) >= 3
    assert trace_data["verification_status"]["verified"] is True
    assert trace_data["final_result"] is not None


def test_api_execute_task_not_found(client: TestClient):
    """POST /tasks/{task_id}/execute returns 404 for non-existent task."""
    resp = client.post("/tasks/non_existent_task_123/execute")
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()


def test_api_get_task_execution_not_found(client: TestClient):
    """GET /tasks/{task_id}/execution returns 404 for non-existent task."""
    resp = client.get("/tasks/non_existent_task_123/execution")
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()
