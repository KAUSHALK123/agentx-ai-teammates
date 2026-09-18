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
        "n8n_operations_check",
    ]

    def __init__(self, planner: Optional[AIPlanner] = None):
        self.planner = planner or AIPlanner()

    async def plan(self, user_request: str, task_id: Optional[str] = None) -> StructuredTaskPlan:
        """Formulate an adaptive, structured execution plan for operational requests."""
        import re
        import uuid
        from app.models.plan import PlanStep

        tid = task_id or f"task_{uuid.uuid4().hex[:12]}"
        req_lower = user_request.lower()

        # Scenario 1: High-risk operational actions (data deletion, purge, or destructive changes)
        if re.search(r"\b(delete|destroy|purge|drop|wipe)\b", req_lower):
            steps = [
                PlanStep(
                    step_id=1,
                    action="Retrieve business record to be deleted",
                    type="tool_action",
                    tool_id="get_business_data",
                    status="PENDING",
                ),
                PlanStep(
                    step_id=2,
                    action="Execute high-risk data deletion action",
                    type="tool_action",
                    tool_id="delete_record",
                    status="PENDING",
                ),
                PlanStep(
                    step_id=3,
                    action="Log data deletion in audit activity trail",
                    type="synthesis",
                    tool_id="create_activity",
                    status="PENDING",
                ),
            ]
            return StructuredTaskPlan(
                task_id=tid,
                agent="operations",
                objective=f"Execute operational data modification: {user_request[:60]}",
                steps=steps,
                primary_tool="delete_record",
                plan_summary="High-risk data operation requiring human approval",
            )

        # Scenario 2: Comprehensive multi-step n8n operational workflow
        # Matches:
        # "Run today's operations check and tell me what needs attention."
        # "Process the daily operations workflow."
        # "Generate today's operations report."
        # "Find records that need follow-up."
        # "Run the daily operations check."
        if (
            re.search(r"\b(operations?\s*check|operations?\s*workflow|daily\s*check|operational\s*check|daily\s*operations?|operations?\s*report)\b", req_lower)
            or re.search(r"\b(process|run|execute)\b.*\b(daily|operations?|workflow)\b", req_lower)
            or re.search(r"\bfind\b.*\b(follow-?up|exceptions?)\b", req_lower)
        ):
            steps = [
                PlanStep(
                    step_id=1,
                    action="Retrieve current operational state and transaction summaries",
                    type="tool_action",
                    tool_id="get_business_data",
                    status="PENDING",
                ),
                PlanStep(
                    step_id=2,
                    action="Orchestrate n8n daily business check, evaluate exception rules, and compile report",
                    type="tool_action",
                    tool_id="n8n_operations_check",
                    status="PENDING",
                ),
                PlanStep(
                    step_id=3,
                    action="Log executive operational summary and verified actions in activity history",
                    type="synthesis",
                    tool_id="create_activity",
                    status="PENDING",
                ),
            ]
            return StructuredTaskPlan(
                task_id=tid,
                agent="operations",
                objective=f"Execute daily operational check and exception audit: {user_request[:60]}",
                steps=steps,
                primary_tool="n8n_operations_check",
                plan_summary="Execute daily operational check and exception audit via n8n workflow",
            )

        # Scenario 3: Standard business data review / single record verification
        # Matches:
        # "Check today's business data and identify anything requiring attention."
        # "Verify today's business records."
        if re.search(r"\b(check|review|inspect|audit)\b.*\b(data|records?)\b", req_lower) or "verify" in req_lower:
            steps = [
                PlanStep(
                    step_id=1,
                    action="Retrieve business metric feeds and summary",
                    type="tool_action",
                    tool_id="get_business_data",
                    status="PENDING",
                ),
                PlanStep(
                    step_id=2,
                    action="Verify specific business records for discrepancies",
                    type="tool_action",
                    tool_id="verify_record",
                    status="PENDING",
                ),
                PlanStep(
                    step_id=3,
                    action="Log verified operational inspection in activity audit",
                    type="synthesis",
                    tool_id="create_activity",
                    status="PENDING",
                ),
            ]
            return StructuredTaskPlan(
                task_id=tid,
                agent="operations",
                objective=f"Review business metrics and verify records: {user_request[:60]}",
                steps=steps,
                primary_tool="get_business_data",
                plan_summary="Audit business metrics and verify database records",
            )

        # Fallback to general AI Planner for open-ended operational inquiries
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
