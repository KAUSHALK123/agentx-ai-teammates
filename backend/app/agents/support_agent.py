from typing import List
from app.agents.base import BaseAgent, TaskPlan
from app.models.task import AgentType


class SupportAgent(BaseAgent):
    """Customer Support AI Teammate.
    
    Handles customer inquiries, dispute reviews, order issues, and ticket lookups.
    """

    agent_type: AgentType = AgentType.SUPPORT
    name: str = "Support Teammate"
    role: str = "Customer Resolution & Support Specialist"
    description: str = "Resolves customer support tickets, checks order histories, and handles customer inquiries."
    available_tools: List[str] = ["ticket_lookup"]

    async def plan(self, user_request: str) -> TaskPlan:
        """Create structured execution plan for support request."""
        return TaskPlan(
            steps=[
                "Parse user support request and extract reference tokens",
                "Execute ticket_lookup against customer support system",
                "Synthesize support status and formulate resolution",
            ],
            primary_tool="ticket_lookup",
            plan_summary="Investigate ticket and order history to formulate resolution.",
        )
