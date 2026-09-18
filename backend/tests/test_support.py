import pytest
from fastapi.testclient import TestClient
from app.agents.support_agent import SupportAgent
from app.main import app
from app.models.approval import ApprovalStatus, RiskLevel
from app.models.plan import StructuredTaskPlan
from app.models.support import (
    ResponseStrategy,
    ReviewSentiment,
    SupportCaseStatus,
    SupportIntent,
    SupportSeverity,
)
from app.models.task import AgentType, Task, TaskStatus
from app.services.approval_policy import get_approval_policy
from app.services.approval_store import get_approval_store
from app.services.data_service import (
    DemoDataService,
    get_data_service,
    normalize_customer_id,
    normalize_order_id,
    normalize_transaction_id,
)
from app.services.execution_engine import TaskExecutionEngine
from app.services.orchestrator import TaskOrchestrator
from app.services.support_analyzer import SupportAnalyzer
from app.services.task_store import get_task_store
from app.services.tool_executor import get_tool_executor
from app.tools.support_tools import (
    EscalateSupportCaseTool,
    IssueDemoRefundTool,
    PrepareCustomerResponseTool,
)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def data_service():
    return DemoDataService()


# =======================================================
# 1. Support Intent & Severity Classification Tests
# =======================================================

def test_intent_classification_order_issue():
    res = SupportAnalyzer.classify_intent("Customer C001 has a damaged order package.")
    assert res.intent in [SupportIntent.ORDER_ISSUE, SupportIntent.CUSTOMER_COMPLAINT]
    assert res.confidence >= 0.8
    assert res.extracted_entities.get("customer_id") == "CUST-001"


def test_intent_classification_delayed_order():
    res = SupportAnalyzer.classify_intent("Investigate why customer C001's order is delayed.")
    assert res.intent == SupportIntent.DELAYED_ORDER
    assert res.confidence >= 0.85
    assert res.severity in [SupportSeverity.MEDIUM, SupportSeverity.HIGH]


def test_intent_classification_payment_issue():
    res = SupportAnalyzer.classify_intent("Customer C001 says their payment went through but their order is still pending.")
    assert res.intent == SupportIntent.PAYMENT_ISSUE
    assert res.confidence >= 0.85
    assert res.severity in [SupportSeverity.MEDIUM, SupportSeverity.HIGH]


def test_intent_classification_refund_request():
    res = SupportAnalyzer.classify_intent("Refund customer C001 for the failed transaction.")
    assert res.intent == SupportIntent.REFUND_REQUEST
    assert res.confidence >= 0.85
    assert res.severity in [SupportSeverity.HIGH, SupportSeverity.CRITICAL]


def test_intent_classification_return_request():
    res = SupportAnalyzer.classify_intent("Customer wants to return item and request pickup for ORD-1001.")
    assert res.intent == SupportIntent.RETURN_REQUEST
    assert res.extracted_entities.get("order_id") == "ORD-1001"


def test_intent_classification_escalation():
    res = SupportAnalyzer.classify_intent("Customer threatens legal lawsuit and demands immediate escalation to supervisor.")
    assert res.intent == SupportIntent.ESCALATION
    assert res.severity == SupportSeverity.CRITICAL


def test_intent_classification_review():
    res = SupportAnalyzer.classify_intent("Customer review: 1 star! Terrible delay on delivery!")
    assert res.intent == SupportIntent.CUSTOMER_REVIEW


def test_severity_classification_explainable():
    # Critical due to legal keywords
    sev_crit = SupportAnalyzer.classify_severity("I am speaking to my lawyer about this fraud transaction.")
    assert sev_crit == SupportSeverity.CRITICAL

    # High due to financial refund
    sev_high = SupportAnalyzer.classify_severity("Please refund my failed payment of Rs. 14500.")
    assert sev_high == SupportSeverity.HIGH

    # Medium due to delay
    sev_med = SupportAnalyzer.classify_severity("My delivery ORD-1002 is delayed.")
    assert sev_med == SupportSeverity.MEDIUM

    # Low for general question
    sev_low = SupportAnalyzer.classify_severity("What are your business support hours?")
    assert sev_low == SupportSeverity.LOW


# =======================================================
# 2. Customer Context & Normalization Tests
# =======================================================

@pytest.mark.asyncio
async def test_id_normalization(data_service):
    assert normalize_customer_id("C001") == "CUST-001"
    assert normalize_customer_id("CUST-002") == "CUST-002"
    assert normalize_order_id("O1001") == "ORD-1001"
    assert normalize_transaction_id("T5001") == "TXN-5001"

    # Verify data service resolves both normalized and shorthand identifiers
    cust1 = await data_service.get_customer("C001")
    assert cust1 is not None
    assert cust1.customer_id == "CUST-001"
    assert cust1.name == "Alice Sharma"

    ord1 = await data_service.get_order("ORD-1001")
    assert ord1 is not None
    assert ord1.customer_id == "CUST-001"

    txn1 = await data_service.get_transaction("TXN-5001")
    assert txn1 is not None
    assert txn1.payment_status == "successful"


# =======================================================
# 3. Customer Review Support Tests
# =======================================================

def test_customer_review_negative_delayed():
    review = "Terrible experience with AgentX! Order ORD-1002 was delayed for a week without any communication. 1 star!"
    analysis = SupportAnalyzer.analyze_review(review)

    assert analysis.sentiment == ReviewSentiment.NEGATIVE
    assert analysis.intent == SupportIntent.DELAYED_ORDER
    assert analysis.severity in [SupportSeverity.MEDIUM, SupportSeverity.HIGH]
    assert analysis.recommended_strategy == ResponseStrategy.APOLOGIZE_AND_UPDATE
    assert len(analysis.available_options) == 5
    assert analysis.approval_required is True
    assert "apologize" in analysis.draft_response.lower()


def test_customer_review_payment_compensation():
    review = "Double charged for my order and payment deducted twice! Very disappointed."
    analysis = SupportAnalyzer.analyze_review(review)

    assert analysis.sentiment == ReviewSentiment.NEGATIVE
    assert analysis.recommended_strategy == ResponseStrategy.OFFER_COMPENSATION
    assert analysis.approval_required is True


def test_customer_review_missing_context():
    review = "Horrible customer support, nobody answered my query."
    analysis = SupportAnalyzer.analyze_review(review)

    assert analysis.sentiment == ReviewSentiment.NEGATIVE
    assert analysis.recommended_strategy == ResponseStrategy.REQUEST_MORE_INFO


# =======================================================
# 4. Controlled Support Tools Unit Tests
# =======================================================

@pytest.mark.asyncio
async def test_prepare_customer_response_tool(data_service):
    tool = PrepareCustomerResponseTool(data_service=data_service)
    result = await tool.execute(
        customer_id="CUST-001",
        order_id="ORD-1002",
        issue_summary="order delay inquiry",
        proposed_resolution="expedited air shipping update",
        strategy="Apologize + Provide Update",
    )

    assert result.success is True
    assert "Alice Sharma" in result.data["customer_name"]
    assert "ORD-1002" in result.data["customer_response"]
    assert result.data["external_dispatch_approved"] is False


@pytest.mark.asyncio
async def test_issue_demo_refund_tool(data_service):
    tool = IssueDemoRefundTool(data_service=data_service)
    result = await tool.execute(
        transaction_id="TXN-5003",
        order_id="ORD-1003",
        customer_id="CUST-002",
        amount=890.0,
        reason="Transaction failed at payment gateway",
    )

    assert result.success is True
    assert result.data["status"] == "refunded"
    assert result.data["amount"] == 890.0

    # Verify transaction payment_status in data store changed to refunded
    txn = await data_service.get_transaction("TXN-5003")
    assert txn.payment_status == "refunded"


@pytest.mark.asyncio
async def test_escalate_support_case_tool(data_service):
    tool = EscalateSupportCaseTool(data_service=data_service)
    result = await tool.execute(
        task_id="task_test_esc",
        customer_id="CUST-001",
        reason="Customer requires manual executive review for repeated order damage",
        severity="HIGH",
        recommended_human_action="Call customer and offer account credit",
    )

    assert result.success is True
    assert result.data["escalated"] is True
    assert result.data["severity"] == "HIGH"

    # Verify support case was persisted
    case = await data_service.get_support_case(result.data["case_id"])
    assert case is not None
    assert case.status == SupportCaseStatus.ESCALATED


# =======================================================
# 5. DEMO SCENARIO A — ORDER INVESTIGATION
# =======================================================

@pytest.mark.asyncio
async def test_scenario_a_order_investigation():
    """SCENARIO A: 'Investigate why customer C001's order is delayed.'
    
    Expected: lookup_customer -> lookup_order -> investigate status -> verify -> final result.
    """
    engine = TaskExecutionEngine()
    support = SupportAgent()
    task = Task(
        task_id="task_scenario_a",
        user_request="Investigate why customer C001's order is delayed.",
        selected_agent=AgentType.SUPPORT,
        status=TaskStatus.CREATED,
    )

    plan = await support.plan(task.user_request, task_id=task.task_id)
    assert plan.agent == "support"
    tool_ids = [s.tool_id for s in plan.steps if s.tool_id]
    assert "lookup_customer" in tool_ids
    assert "lookup_order" in tool_ids

    executed_task = await engine.execute_task(task, support, plan)

    assert executed_task.status == TaskStatus.COMPLETED
    assert executed_task.verification_result["verified"] is True
    assert executed_task.result["agent"] == "support"
    assert executed_task.result["status"] == "COMPLETED"
    assert "CUST-001" in executed_task.result["customer"]
    assert len(executed_task.result["actions_performed"]) >= 3


# =======================================================
# 6. DEMO SCENARIO B — PAYMENT ISSUE
# =======================================================

@pytest.mark.asyncio
async def test_scenario_b_payment_issue():
    """SCENARIO B: 'Customer C001 says their payment went through but their order is still pending.'
    
    Expected: lookup_customer -> lookup_order -> lookup_transaction -> analyze mismatch -> recommend resolution -> verify -> result.
    """
    engine = TaskExecutionEngine()
    support = SupportAgent()
    task = Task(
        task_id="task_scenario_b",
        user_request="Customer C001 says their payment went through but their order is still pending.",
        selected_agent=AgentType.SUPPORT,
        status=TaskStatus.CREATED,
    )

    plan = await support.plan(task.user_request, task_id=task.task_id)
    tool_ids = [s.tool_id for s in plan.steps if s.tool_id]
    assert "lookup_customer" in tool_ids
    assert "lookup_order" in tool_ids
    assert "lookup_transaction" in tool_ids

    executed_task = await engine.execute_task(task, support, plan)

    assert executed_task.status == TaskStatus.COMPLETED
    assert executed_task.verification_result["verified"] is True
    assert "CUST-001" in executed_task.result["customer"]
    assert executed_task.result["actions_performed"] is not None


# =======================================================
# 7. DEMO SCENARIO C — HIGH-RISK ACTION & HUMAN APPROVAL
# =======================================================

@pytest.mark.asyncio
async def test_scenario_c_high_risk_refund_approval_flow():
    """SCENARIO C: 'Refund customer C001 for the failed transaction.'
    
    Expected: investigate -> determine refund action -> WAITING_FOR_APPROVAL -> approval -> execute -> verify -> COMPLETED.
    """
    engine = TaskExecutionEngine()
    support = SupportAgent()
    task = Task(
        task_id="task_scenario_c_approve",
        user_request="Refund customer C001 for the failed transaction.",
        selected_agent=AgentType.SUPPORT,
        status=TaskStatus.CREATED,
    )

    plan = await support.plan(task.user_request, task_id=task.task_id)
    assert any(s.tool_id == "issue_demo_refund" for s in plan.steps)

    # 1. First execution run: pauses at WAITING_FOR_APPROVAL
    paused_task = await engine.execute_task(task, support, plan)

    assert paused_task.status == TaskStatus.WAITING_FOR_APPROVAL
    assert paused_task.approval_required is True
    assert paused_task.current_approval_id is not None
    assert paused_task.result["risk_level"] == "HIGH"
    assert "CUST-001" in paused_task.result["customer"]

    # 2. Human supervisor reviews and approves action
    appr_store = get_approval_store()
    approval_rec = await appr_store.get_approval(paused_task.current_approval_id)
    assert approval_rec is not None
    assert approval_rec.status == ApprovalStatus.PENDING

    resumed_task = await engine.resume_task_after_approval(
        task=paused_task,
        approval=approval_rec,
        agent=support,
        resolved_by="lead_support_supervisor",
    )

    # 3. Resumed task finishes with refund execution and verification
    assert resumed_task.status == TaskStatus.COMPLETED
    assert resumed_task.verification_result["verified"] is True
    assert resumed_task.result["status"] == "COMPLETED"


@pytest.mark.asyncio
async def test_scenario_c_rejection_flow():
    """Test rejection branch of Scenario C: supervisor rejects refund action."""
    engine = TaskExecutionEngine()
    support = SupportAgent()
    task = Task(
        task_id="task_scenario_c_reject",
        user_request="Refund customer C001 for the failed transaction.",
        selected_agent=AgentType.SUPPORT,
        status=TaskStatus.CREATED,
    )

    plan = await support.plan(task.user_request, task_id=task.task_id)
    paused_task = await engine.execute_task(task, support, plan)

    assert paused_task.status == TaskStatus.WAITING_FOR_APPROVAL

    appr_store = get_approval_store()
    approval_rec = await appr_store.get_approval(paused_task.current_approval_id)

    stopped_task = await engine.stop_task_after_rejection(
        task=paused_task,
        approval=approval_rec,
        rejection_reason="Duplicate refund request already submitted yesterday",
        resolved_by="compliance_manager",
    )

    assert stopped_task.status == TaskStatus.FAILED
    assert "Duplicate refund" in stopped_task.result["summary"]
    assert stopped_task.verification_result["verified"] is False


# =======================================================
# 8. DEMO SCENARIO D — CUSTOMER REVIEW
# =======================================================

@pytest.mark.asyncio
async def test_scenario_d_customer_review():
    """SCENARIO D: Fictional negative customer review.
    
    Expected: analyze sentiment -> identify intent/severity -> retrieve context -> recommend response -> approval required -> verify.
    """
    engine = TaskExecutionEngine()
    support = SupportAgent()
    review_input = "Customer review from C001: 1 star. My order hasn't arrived and tracking is completely delayed! Worst service!"
    
    task = Task(
        task_id="task_scenario_d",
        user_request=review_input,
        selected_agent=AgentType.SUPPORT,
        status=TaskStatus.CREATED,
    )

    plan = await support.plan(task.user_request, task_id=task.task_id)
    executed_task = await engine.execute_task(task, support, plan)

    assert executed_task.status == TaskStatus.COMPLETED
    assert executed_task.verification_result["verified"] is True
    assert "CUST-001" in executed_task.result["customer"]


# =======================================================
# 9. Support API Endpoint Tests
# =======================================================

def test_api_support_analyze_delayed_order(client):
    response = client.post(
        "/support/analyze",
        json={"message": "Investigate why customer C001's order is delayed.", "customer_id": "CUST-001"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "DELAYED_ORDER"
    assert data["severity"] in ["MEDIUM", "HIGH"]
    assert data["customer_context"] is not None
    assert data["customer_context"]["customer"]["customer_id"] == "CUST-001"
    assert len(data["response_options"]) > 0


def test_api_support_analyze_negative_review(client):
    response = client.post(
        "/api/v1/support/analyze",
        json={"message": "Review: 1 star. Terrible delay on delivery for order ORD-1002!"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["sentiment"] == "NEGATIVE"
    assert data["approval_required"] is True
    assert data["recommended_strategy"] == "Apologize + Provide Update"
    assert data["draft_response"] is not None


def test_api_support_analyze_empty_validation(client):
    response = client.post(
        "/support/analyze",
        json={"message": "   "},
    )
    assert response.status_code == 422


# =======================================================
# 10. Support Escalation & Tool Failure Resilience
# =======================================================

@pytest.mark.asyncio
async def test_support_escalation_flow():
    """Verify support escalation when policy requires human intervention."""
    engine = TaskExecutionEngine()
    support = SupportAgent()
    task = Task(
        task_id="task_escalate_flow",
        user_request="Customer C001 threatens legal lawsuit and demands immediate escalation.",
        selected_agent=AgentType.SUPPORT,
        status=TaskStatus.CREATED,
    )

    plan = await support.plan(task.user_request, task_id=task.task_id)
    executed = await engine.execute_task(task, support, plan)

    # When escalated, verifier checks case and sets status to ESCALATED
    assert executed.status == TaskStatus.ESCALATED
    assert executed.verification_result["requires_human_review"] is True


@pytest.mark.asyncio
async def test_support_tool_failure_handling(data_service):
    """Verify tool failure handling when requested order is not found."""
    from app.tools.implementations import LookupOrderTool
    tool = LookupOrderTool(data_service=data_service)
    result = await tool.execute(order_id="ORD-NONEXISTENT-999")

    assert result.success is False
    assert "not found" in result.error.lower()
