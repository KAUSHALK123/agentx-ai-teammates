from typing import List, Optional
from app.agents.base import AgentCapability, BaseAgent, StructuredTaskPlan
from app.models.task import AgentType
from app.services.planner import AIPlanner


class SalesAgent(BaseAgent):
    """Sales AI Teammate.
    
    Specialized in lead qualification, sales follow-ups, customer/product context,
    sales communication, task preparation, and CRM-related actions.
    """

    agent_id: str = "sales"
    agent_type: AgentType = AgentType.SALES
    name: str = "Sales Teammate"
    role: str = "Commercial Account & Lead Specialist"
    description: str = (
        "Specialized AI teammate for evaluating commercial opportunities, qualifying inbound "
        "leads, tailoring product proposals, and orchestrating CRM follow-ups."
    )

    responsibilities: List[str] = [
        "lead qualification",
        "lead follow-up",
        "customer/product context",
        "sales communication",
        "sales task preparation",
        "CRM-related actions",
    ]

    capabilities: List[AgentCapability] = [
        AgentCapability(
            name="qualify_lead",
            description="Evaluate prospect fit, budget authority, deal size, and timeline criteria.",
            category="qualification",
        ),
        AgentCapability(
            name="analyze_lead",
            description="Assess organizational scale, industry vertical, and commercial synergy.",
            category="analysis",
        ),
        AgentCapability(
            name="prepare_followup",
            description="Draft personalized high-conversion sales outreach and proposal overviews.",
            category="communication",
        ),
        AgentCapability(
            name="recommend_next_action",
            description="Prescribe strategic deal progression steps, enterprise terms, or demo milestones.",
            category="strategy",
        ),
    ]

    system_instructions: str = (
        "You are the AgentX Commercial & Sales Teammate. Your objective is to accelerate deals, "
        "evaluate prospect readiness, ensure accurate pricing models, and return high-impact, structured "
        "commercial action plans."
    )

    available_tools: List[str] = [
        "lookup_customer",
        "lookup_lead",
        "sales_process_lead",
        "n8n_process_lead",
        "update_lead",
        "n8n_send_followup",
        "create_activity",
    ]

    def __init__(self, planner: Optional[AIPlanner] = None):
        self.planner = planner or AIPlanner()

    async def plan(self, user_request: str, task_id: Optional[str] = None) -> StructuredTaskPlan:
        """Formulate an adaptive, structured execution plan for commercial requests."""
        import re
        import uuid
        from app.models.plan import PlanStep

        tid = task_id or f"task_{uuid.uuid4().hex[:12]}"
        req_lower = user_request.lower()

        # Scenario 1: External follow-up dispatch (HIGH-RISK, requires human approval)
        if re.search(r"\b(send|dispatch|deliver)\b.*\b(follow-?up|email|message|outreach)\b", req_lower):
            steps = [
                PlanStep(
                    step_id=1,
                    action="Verify sales lead profile and contact parameters",
                    type="tool_action",
                    tool_id="lookup_lead",
                    status="PENDING",
                ),
                PlanStep(
                    step_id=2,
                    action="Send approved follow-up email to lead via n8n integration",
                    type="tool_action",
                    tool_id="n8n_send_followup",
                    status="PENDING",
                ),
                PlanStep(
                    step_id=3,
                    action="Record outbound communication delivery in activity log",
                    type="synthesis",
                    tool_id="create_activity",
                    status="PENDING",
                ),
            ]
            return StructuredTaskPlan(
                task_id=tid,
                agent="sales",
                objective=f"Dispatch approved commercial outreach to prospect: {user_request[:60]}",
                steps=steps,
                primary_tool="n8n_send_followup",
                plan_summary="Dispatch approved follow-up email via n8n integration",
            )

        # Scenario 2: Lead processing, qualification, and follow-up preparation via n8n workflow
        if re.search(r"\b(follow-?ups?|proposal\w*|qualif\w*|n8n|workflow)\b", req_lower):
            steps = [
                PlanStep(
                    step_id=1,
                    action="Retrieve prospect details and CRM context",
                    type="tool_action",
                    tool_id="lookup_lead",
                    status="PENDING",
                ),
                PlanStep(
                    step_id=2,
                    action="Orchestrate n8n lead qualification workflow and draft proposal",
                    type="tool_action",
                    tool_id="sales_process_lead",
                    status="PENDING",
                ),
                PlanStep(
                    step_id=3,
                    action="Log commercial activity and queue for follow-up review",
                    type="synthesis",
                    tool_id="create_activity",
                    status="PENDING",
                ),
            ]
            return StructuredTaskPlan(
                task_id=tid,
                agent="sales",
                objective=f"Process commercial lead and formulate tailored proposal: {user_request[:60]}",
                steps=steps,
                primary_tool="sales_process_lead",
                plan_summary="Process commercial lead, evaluate qualification via n8n, and draft proposal",
            )

        # Scenario 3: Standard CRM lead update without external orchestration
        if re.search(r"\b(lead|prospect|status)\b", req_lower):
            steps = [
                PlanStep(
                    step_id=1,
                    action="Retrieve prospect details",
                    type="tool_action",
                    tool_id="lookup_lead",
                    status="PENDING",
                ),
                PlanStep(
                    step_id=2,
                    action="Update CRM lead status",
                    type="tool_action",
                    tool_id="update_lead",
                    status="PENDING",
                ),
                PlanStep(
                    step_id=3,
                    action="Log CRM activity record",
                    type="synthesis",
                    tool_id="create_activity",
                    status="PENDING",
                ),
            ]
            return StructuredTaskPlan(
                task_id=tid,
                agent="sales",
                objective=f"Update commercial lead record: {user_request[:60]}",
                steps=steps,
                primary_tool="update_lead",
                plan_summary="Update commercial lead record in CRM",
            )

        # Fallback to general AI Planner for open-ended requests
        capability_names = [c.name for c in self.capabilities]
        return await self.planner.generate_plan(
            user_request=user_request,
            agent_id=self.agent_id,
            agent_name=self.name,
            system_instructions=self.system_instructions,
            capabilities=capability_names,
            available_tools=self.available_tools,
            task_id=task_id,
        )
