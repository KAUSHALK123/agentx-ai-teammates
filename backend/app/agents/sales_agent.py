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
        "update_lead",
        "create_activity",
    ]

    def __init__(self, planner: Optional[AIPlanner] = None):
        self.planner = planner or AIPlanner()

    async def plan(self, user_request: str, task_id: Optional[str] = None) -> StructuredTaskPlan:
        """Formulate a structured execution plan for commercial requests."""
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
