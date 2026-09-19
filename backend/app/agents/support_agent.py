import uuid
from typing import List, Optional
from app.agents.base import AgentCapability, BaseAgent, StructuredTaskPlan
from app.models.plan import PlanStep
from app.models.support import SupportIntent
from app.models.task import AgentType
from app.services.planner import AIPlanner
from app.services.support_analyzer import SupportAnalyzer


class SupportAgent(BaseAgent):
    """Support AI Teammate.
    
    Specialized in customer support, complaints, order/payment issues,
    refund/return requests, review handling, and escalation identification.
    """

    agent_id: str = "support"
    agent_type: AgentType = AgentType.SUPPORT
    name: str = "Support Teammate"
    role: str = "Customer Resolution & Support Specialist"
    description: str = (
        "Specialized AI teammate for resolving customer complaints, investigating "
        "order and payment issues, handling refunds and returns, and escalating critical cases."
    )
    
    responsibilities: List[str] = [
        "customer support",
        "complaints",
        "order/payment issue investigation",
        "refund/return-related requests",
        "customer review handling",
        "escalation identification",
    ]

    capabilities: List[AgentCapability] = [
        AgentCapability(
            name="investigate_customer_issue",
            description="Deep dive into customer problem statements, order timelines, and transactional context.",
            category="investigation",
        ),
        AgentCapability(
            name="analyze_complaint",
            description="Assess customer sentiment, complaint urgency, and SLA impact.",
            category="analysis",
        ),
        AgentCapability(
            name="identify_resolution",
            description="Determine policy-compliant resolution paths such as refunds, replacements, or account credits.",
            category="resolution",
        ),
        AgentCapability(
            name="prepare_response",
            description="Draft empathetic, professional, and clear communications for customers.",
            category="communication",
        ),
        AgentCapability(
            name="escalate_issue",
            description="Detect high-risk, legal, or severe financial disputes requiring human oversight.",
            category="escalation",
        ),
    ]

    system_instructions: str = (
        "You are the AgentX Customer Support Teammate. Your duty is to understand customer "
        "concerns, systematically investigate account/order/payment states, ensure policy compliance, "
        "and produce structured, actionable resolution plans without conversational fluff."
    )

    available_tools: List[str] = [
        "lookup_customer",
        "lookup_order",
        "lookup_transaction",
        "lookup_knowledge",
        "create_activity",
        "prepare_customer_response",
        "issue_demo_refund",
        "escalate_support_case",
        "support_handle_issue",
        "n8n_support_handle_issue",
    ]

    def __init__(self, planner: Optional[AIPlanner] = None):
        self.planner = planner or AIPlanner()

    async def plan(self, user_request: str, task_id: Optional[str] = None) -> StructuredTaskPlan:
        """Formulate an adaptive, structured execution plan for support inquiries."""
        tid = task_id or f"task_{uuid.uuid4().hex[:12]}"
        req_lower = user_request.lower()
        
        # Check for explicit n8n support workflow request
        if any(term in req_lower for term in ["n8n", "handle_support_issue", "support issue", "support workflow", "issue workflow"]):
            steps = [
                PlanStep(
                    step_id=1,
                    action="Identify customer profile and verify account status",
                    type="tool_action",
                    tool_id="lookup_customer",
                    status="PENDING",
                ),
                PlanStep(
                    step_id=2,
                    action="Orchestrate n8n customer support issue resolution workflow",
                    type="tool_action",
                    tool_id="support_handle_issue",
                    status="PENDING",
                ),
                PlanStep(
                    step_id=3,
                    action="Log customer support activity and update ticket status",
                    type="synthesis",
                    tool_id="create_activity",
                    status="PENDING",
                ),
            ]
            return StructuredTaskPlan(
                task_id=tid,
                agent=self.agent_id,
                objective=f"Process customer support issue via n8n: {user_request[:60]}",
                steps=steps,
                primary_tool="support_handle_issue",
                plan_summary="Process support issue via n8n workflow",
            )
        
        # Analyze support intent and entities
        classification = SupportAnalyzer.classify_intent(user_request)
        intent = classification.intent

        # Check if policy or knowledge lookup is relevant
        req_lower = user_request.lower()
        is_policy_query = any(kw in req_lower for kw in ["policy", "rule", "condition", "sla", "guideline", "allowed", "allow", "eligib", "faq", "what does"])

        if is_policy_query:
            steps = [
                PlanStep(
                    step_id=1,
                    action="Search business knowledge graph for relevant policies and rules",
                    type="tool_action",
                    tool_id="lookup_knowledge",
                    input={"query": user_request},
                    status="PENDING",
                ),
                PlanStep(
                    step_id=2,
                    action="Identify customer profile and verify account status",
                    type="tool_action",
                    tool_id="lookup_customer",
                    status="PENDING",
                ),
                PlanStep(
                    step_id=3,
                    action="Prepare customer response based on retrieved policy context",
                    type="tool_action",
                    tool_id="prepare_customer_response",
                    status="PENDING",
                ),
                PlanStep(
                    step_id=4,
                    action="Log resolution activity and policy decision record",
                    type="synthesis",
                    tool_id="create_activity",
                    status="PENDING",
                ),
            ]
            objective = f"Retrieve business policy and formulate resolution for: {user_request[:60]}"
            return StructuredTaskPlan(task_id=tid, agent=self.agent_id, objective=objective, steps=steps)

        # Build intent-adapted plan steps
        if intent == SupportIntent.REFUND_REQUEST:
            steps = [
                PlanStep(
                    step_id=1,
                    action="Identify customer profile and verify account eligibility",
                    type="tool_action",
                    tool_id="lookup_customer",
                    status="PENDING",
                ),
                PlanStep(
                    step_id=2,
                    action="Inspect transaction status and verify payment details",
                    type="tool_action",
                    tool_id="lookup_transaction",
                    status="PENDING",
                ),
                PlanStep(
                    step_id=3,
                    action="Process refund for failed transaction",
                    type="tool_action",
                    tool_id="issue_demo_refund",
                    status="PENDING",
                ),
                PlanStep(
                    step_id=4,
                    action="Log resolution and update activity record",
                    type="synthesis",
                    tool_id="create_activity",
                    status="PENDING",
                ),

            ]
            objective = f"Investigate refund request and process resolution for: {user_request[:60]}"

        elif intent in [SupportIntent.DELAYED_ORDER, SupportIntent.ORDER_ISSUE]:
            steps = [
                PlanStep(
                    step_id=1,
                    action="Identify customer profile and verify account status",
                    type="tool_action",
                    tool_id="lookup_customer",
                    status="PENDING",
                ),
                PlanStep(
                    step_id=2,
                    action="Retrieve customer order fulfillment and tracking details",
                    type="tool_action",
                    tool_id="lookup_order",
                    status="PENDING",
                ),
                PlanStep(
                    step_id=3,
                    action="Check payment reconciliation and settlement status",
                    type="tool_action",
                    tool_id="lookup_transaction",
                    status="PENDING",
                ),
                PlanStep(
                    step_id=4,
                    action="Prepare customer update and resolution response",
                    type="tool_action",
                    tool_id="prepare_customer_response",
                    status="PENDING",
                ),
                PlanStep(
                    step_id=5,
                    action=(
                        "Send customer response email and log resolution activity"
                        if any(w in user_request.lower() for w in ["email", "message", "send", "dispatch"])
                        else "Log customer support resolution activity"
                    ),
                    type="synthesis",
                    tool_id="create_activity",
                    status="PENDING",
                ),
            ]

            objective = f"Investigate delayed order fulfillment and formulate resolution for: {user_request[:60]}"

        elif intent in [SupportIntent.PAYMENT_ISSUE, SupportIntent.TRANSACTION_ISSUE]:
            steps = [
                PlanStep(
                    step_id=1,
                    action="Identify customer profile and verify account status",
                    type="tool_action",
                    tool_id="lookup_customer",
                    status="PENDING",
                ),
                PlanStep(
                    step_id=2,
                    action="Retrieve customer order details to investigate payment mismatch",
                    type="tool_action",
                    tool_id="lookup_order",
                    status="PENDING",
                ),
                PlanStep(
                    step_id=3,
                    action="Lookup payment transaction and settlement status",
                    type="tool_action",
                    tool_id="lookup_transaction",
                    status="PENDING",
                ),
                PlanStep(
                    step_id=4,
                    action="Prepare customer explanation and resolution response",
                    type="tool_action",
                    tool_id="prepare_customer_response",
                    status="PENDING",
                ),
                PlanStep(
                    step_id=5,
                    action=(
                        "Send customer response email and log resolution activity"
                        if any(w in user_request.lower() for w in ["email", "message", "send", "dispatch"])
                        else "Log payment mismatch resolution record"
                    ),
                    type="synthesis",
                    tool_id="create_activity",
                    status="PENDING",
                ),
            ]
            objective = f"Investigate payment mismatch and reconcile transaction for: {user_request[:60]}"

        elif intent == SupportIntent.CUSTOMER_REVIEW:
            steps = [
                PlanStep(
                    step_id=1,
                    action="Identify customer profile and previous activity",
                    type="tool_action",
                    tool_id="lookup_customer",
                    status="PENDING",
                ),
                PlanStep(
                    step_id=2,
                    action="Analyze review sentiment and synthesize recommended response",
                    type="tool_action",
                    tool_id="prepare_customer_response",
                    status="PENDING",
                ),
                PlanStep(
                    step_id=3,
                    action="Record customer review response strategy in activity log",
                    type="synthesis",
                    tool_id="create_activity",
                    status="PENDING",
                ),
            ]
            objective = f"Analyze customer review sentiment and formulate strategy for: {user_request[:60]}"

        elif intent == SupportIntent.ESCALATION:
            steps = [
                PlanStep(
                    step_id=1,
                    action="Identify customer profile",
                    type="tool_action",
                    tool_id="lookup_customer",
                    status="PENDING",
                ),
                PlanStep(
                    step_id=2,
                    action="Escalate high-risk or unresolved case to human supervisor",
                    type="tool_action",
                    tool_id="escalate_support_case",
                    status="PENDING",
                ),
                PlanStep(
                    step_id=3,
                    action="Log escalation record in activity history",
                    type="synthesis",
                    tool_id="create_activity",
                    status="PENDING",
                ),
            ]
            objective = f"Escalate support case for: {user_request[:60]}"

        else:
            steps = [
                PlanStep(
                    step_id=1,
                    action="Identify customer profile and verify account status",
                    type="tool_action",
                    tool_id="lookup_customer",
                    status="PENDING",
                ),
                PlanStep(
                    step_id=2,
                    action="Retrieve customer order fulfillment and tracking details",
                    type="tool_action",
                    tool_id="lookup_order",
                    status="PENDING",
                ),
                PlanStep(
                    step_id=3,
                    action="Lookup payment transaction and settlement status",
                    type="tool_action",
                    tool_id="lookup_transaction",
                    status="PENDING",
                ),
                PlanStep(
                    step_id=4,
                    action="Prepare customer resolution response",
                    type="tool_action",
                    tool_id="prepare_customer_response",
                    status="PENDING",
                ),
                PlanStep(
                    step_id=5,
                    action=(
                        "Send customer response email and log resolution activity"
                        if any(w in user_request.lower() for w in ["email", "message", "send", "dispatch"])
                        else "Log customer support resolution activity"
                    ),
                    type="synthesis",
                    tool_id="create_activity",
                    status="PENDING",
                ),
            ]

            objective = f"Investigate customer issue and formulate resolution for: {user_request[:60]}"

        return StructuredTaskPlan(
            task_id=tid,
            agent=self.agent_id,
            objective=objective,
            steps=steps,
        )
