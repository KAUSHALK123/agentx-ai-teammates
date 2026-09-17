from typing import List, Optional
from app.agents.base import AgentCapability, BaseAgent, StructuredTaskPlan
from app.models.task import AgentType
from app.services.planner import AIPlanner


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

    available_tools: List[str] = ["ticket_lookup"]

    def __init__(self, planner: Optional[AIPlanner] = None):
        self.planner = planner or AIPlanner()

    async def plan(self, user_request: str, task_id: Optional[str] = None) -> StructuredTaskPlan:
        """Formulate a structured execution plan for support inquiries."""
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
