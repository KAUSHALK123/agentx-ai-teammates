from typing import List
from app.agents.base import BaseAgent, TaskPlan
from app.models.task import AgentType


class SalesAgent(BaseAgent):
    """Commercial & Sales AI Teammate.
    
    Handles lead qualification, pricing calculations, product tiers, and enterprise inquiries.
    """

    agent_type: AgentType = AgentType.SALES
    name: str = "Sales Teammate"
    role: str = "Commercial Account & Lead Specialist"
    description: str = "Qualifies inbound sales leads, determines pricing tiers, and handles commercial contracts."
    available_tools: List[str] = ["lead_qualification"]

    async def plan(self, user_request: str) -> TaskPlan:
        """Create structured execution plan for commercial inquiry."""
        return TaskPlan(
            steps=[
                "Parse company scale, volume, and budget from commercial inquiry",
                "Execute lead_qualification through CRM service",
                "Formulate commercial proposal and tier recommendation",
            ],
            primary_tool="lead_qualification",
            plan_summary="Analyze commercial request and qualify lead for appropriate tier.",
        )
