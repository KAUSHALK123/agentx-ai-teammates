from typing import List, Optional
from app.agents.base import AgentCapability, BaseAgent, StructuredTaskPlan
from app.models.task import AgentType
from app.services.planner import AIPlanner


class OperationsAgent(BaseAgent):
    """Operations AI Teammate.
    
    Specialized in business operations, report compilation, data processing,
    record verification, operational workflows, and exception identification.
    """

    agent_id: str = "operations"
    agent_type: AgentType = AgentType.OPERATIONS
    name: str = "Operations Teammate"
    role: str = "Logistics & Operational Workflow Specialist"
    description: str = (
        "Specialized AI teammate for analyzing business data feeds, detecting "
        "operational anomalies, compiling executive reports, and coordinating warehouse workflows."
    )

    responsibilities: List[str] = [
        "business operations",
        "reports",
        "data processing",
        "record verification",
        "operational tasks",
        "identifying exceptions",
        "internal workflow execution",
    ]

    capabilities: List[AgentCapability] = [
        AgentCapability(
            name="analyze_business_data",
            description="Process operational logs, sales reports, and throughput indicators.",
            category="analysis",
        ),
        AgentCapability(
            name="generate_report",
            description="Compile concise summaries, KPIs, and operational audit trails.",
            category="reporting",
        ),
        AgentCapability(
            name="verify_records",
            description="Audit database records, inventory entries, and transaction logs for discrepancies.",
            category="verification",
        ),
        AgentCapability(
            name="identify_exception",
            description="Spot low-stock alerts, logistics delays, fulfillment gaps, and operational anomalies.",
            category="monitoring",
        ),
        AgentCapability(
            name="prepare_operational_action",
            description="Formulate procedural recommendations, warehouse tasks, and reorder triggers.",
            category="execution",
        ),
    ]

    system_instructions: str = (
        "You are the AgentX Operations Teammate. Your focus is data rigor, warehouse/logistics "
        "accuracy, anomaly detection, and providing structured operational execution plans."
    )

    available_tools: List[str] = [
        "get_business_data",
        "verify_record",
        "create_activity",
    ]

    def __init__(self, planner: Optional[AIPlanner] = None):
        self.planner = planner or AIPlanner()

    async def plan(self, user_request: str, task_id: Optional[str] = None) -> StructuredTaskPlan:
        """Formulate a structured execution plan for operational tasks."""
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
