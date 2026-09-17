import json
import logging
import re
import uuid
from typing import List, Optional
from app.models.plan import PlanStep, StructuredTaskPlan
from app.core.llm import BaseLLMProvider, get_llm_provider

logger = logging.getLogger(__name__)


class AIPlanner:
    """Intelligent planning engine that generates structured task execution plans."""

    def __init__(self, llm_provider: Optional[BaseLLMProvider] = None):
        self.llm = llm_provider or get_llm_provider()

    async def generate_plan(
        self,
        user_request: str,
        agent_id: str,
        agent_name: str,
        system_instructions: str,
        capabilities: List[str],
        available_tools: List[str],
        task_id: Optional[str] = None,
    ) -> StructuredTaskPlan:
        """Formulate a structured task plan for an AI teammate."""
        tid = task_id or f"task_{uuid.uuid4().hex[:12]}"
        
        system_prompt = (
            f"You are the planner for {agent_name} (ID: {agent_id}) in AgentX.\n"
            f"Your instructions: {system_instructions}\n"
            f"Your capabilities: {', '.join(capabilities)}\n"
            f"Available tools: {', '.join(available_tools) if available_tools else 'None'}\n\n"
            "Rules for planning:\n"
            "1. Output ONLY valid JSON, without any conversational preamble or markdown backticks.\n"
            "2. Break down the user request into 3 to 5 clear, actionable steps.\n"
            "3. Use step types: 'investigation', 'tool_action', 'verification', 'synthesis'.\n"
            "4. NEVER include internal reasoning, hidden thoughts, or chain-of-thought.\n"
            "Format:\n"
            "{\n"
            '  "objective": "Concise summary of the task objective",\n'
            '  "steps": [\n'
            '    {"step_id": 1, "action": "Action description", "type": "investigation", "status": "pending"},\n'
            '    {"step_id": 2, "action": "Action description", "type": "tool_action", "status": "pending"},\n'
            '    {"step_id": 3, "action": "Action description", "type": "verification", "status": "pending"}\n'
            "  ]\n"
            "}"
        )

        user_prompt = f"User Request: {user_request}\nGenerate structured execution plan:"

        try:
            raw_response = await self.llm.generate_text(user_prompt, system_instruction=system_prompt)
            plan = self._parse_llm_response(raw_response, tid, agent_id)
            if plan:
                return plan
        except Exception as exc:
            logger.warning("LLM planning encountered exception: %s. Using resilient template.", exc)

        return self._generate_fallback_plan(user_request, agent_id, tid)

    def _parse_llm_response(self, text: str, task_id: str, agent_id: str) -> Optional[StructuredTaskPlan]:
        """Safely extract and parse JSON from LLM output."""
        if not text or not text.strip():
            return None

        # Clean markdown code blocks if present
        cleaned = text.strip()
        if "```" in cleaned:
            match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned)
            if match:
                cleaned = match.group(1).strip()

        try:
            data = json.loads(cleaned)
            objective = data.get("objective", f"Execute {agent_id} request")
            raw_steps = data.get("steps", [])
            
            steps = []
            for idx, s in enumerate(raw_steps, start=1):
                steps.append(
                    PlanStep(
                        step_id=s.get("step_id", idx),
                        action=s.get("action", f"Step {idx}"),
                        type=s.get("type", "investigation"),
                        status="pending",
                    )
                )
            
            if steps:
                return StructuredTaskPlan(
                    task_id=task_id,
                    agent=agent_id,
                    objective=objective,
                    steps=steps,
                )
        except Exception as err:
            logger.warning("Failed to parse LLM JSON plan: %s", err)

        return None

    def _generate_fallback_plan(self, user_request: str, agent_id: str, task_id: str) -> StructuredTaskPlan:
        """Deterministic structured fallback plan for offline mode or test resilience."""
        if agent_id == "support":
            return StructuredTaskPlan(
                task_id=task_id,
                agent="support",
                objective=f"Investigate customer issue and formulate resolution for: {user_request[:60]}",
                steps=[
                    PlanStep(
                        step_id=1,
                        action="Analyze customer issue details and extract account/order tokens",
                        type="investigation",
                        status="pending",
                    ),
                    PlanStep(
                        step_id=2,
                        action="Perform ticket and order lookup in customer support system",
                        type="tool_action",
                        status="pending",
                    ),
                    PlanStep(
                        step_id=3,
                        action="Verify payment/delivery status and evaluate escalation criteria",
                        type="verification",
                        status="pending",
                    ),
                    PlanStep(
                        step_id=4,
                        action="Synthesize customer response and prepare resolution record",
                        type="synthesis",
                        status="pending",
                    ),
                ],
            )
        elif agent_id == "sales":
            return StructuredTaskPlan(
                task_id=task_id,
                agent="sales",
                objective=f"Qualify sales inquiry and prepare commercial follow-up for: {user_request[:60]}",
                steps=[
                    PlanStep(
                        step_id=1,
                        action="Extract prospect company scale, requirements, and deal intent",
                        type="investigation",
                        status="pending",
                    ),
                    PlanStep(
                        step_id=2,
                        action="Evaluate lead qualification criteria and determine pricing tier in CRM",
                        type="tool_action",
                        status="pending",
                    ),
                    PlanStep(
                        step_id=3,
                        action="Validate commercial eligibility and enterprise discount thresholds",
                        type="verification",
                        status="pending",
                    ),
                    PlanStep(
                        step_id=4,
                        action="Draft personalized commercial follow-up and next action plan",
                        type="synthesis",
                        status="pending",
                    ),
                ],
            )
        else:  # operations
            return StructuredTaskPlan(
                task_id=task_id,
                agent="operations",
                objective=f"Analyze operational records and identify actionable exceptions for: {user_request[:60]}",
                steps=[
                    PlanStep(
                        step_id=1,
                        action="Parse operational parameters, SKU identifiers, and dataset scope",
                        type="investigation",
                        status="pending",
                    ),
                    PlanStep(
                        step_id=2,
                        action="Query inventory status and fulfillment data from ERP system",
                        type="tool_action",
                        status="pending",
                    ),
                    PlanStep(
                        step_id=3,
                        action="Inspect records for discrepancies, stock anomalies, or logistics delays",
                        type="verification",
                        status="pending",
                    ),
                    PlanStep(
                        step_id=4,
                        action="Generate operational report and summarize corrective actions",
                        type="synthesis",
                        status="pending",
                    ),
                ],
            )
