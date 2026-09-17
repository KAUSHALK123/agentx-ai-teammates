from typing import List
from app.agents.base import BaseAgent, TaskPlan
from app.models.task import AgentType


class OperationsAgent(BaseAgent):
    """Operations & Logistics AI Teammate.
    
    Handles inventory tracking, warehouse fulfillment queries, and operational logistics.
    """

    agent_type: AgentType = AgentType.OPERATIONS
    name: str = "Operations Teammate"
    role: str = "Logistics & Inventory Specialist"
    description: str = "Monitors warehouse stock levels, tracks logistics shipments, and validates inventory."
    available_tools: List[str] = ["inventory_status"]

    async def plan(self, user_request: str) -> TaskPlan:
        """Create structured execution plan for operations request."""
        return TaskPlan(
            steps=[
                "Extract item identifier or SKU from operations query",
                "Execute inventory_status check against warehouse ERP",
                "Synthesize fulfillment status and stock availability",
            ],
            primary_tool="inventory_status",
            plan_summary="Query inventory ERP and assess stock availability.",
        )
