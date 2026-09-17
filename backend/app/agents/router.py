import logging
import re
from typing import Dict, List, Optional, Tuple
from pydantic import BaseModel, Field
from app.agents.base import BaseAgent
from app.agents.support_agent import SupportAgent
from app.agents.sales_agent import SalesAgent
from app.agents.operations_agent import OperationsAgent
from app.core.llm import BaseLLMProvider, get_llm_provider
from app.models.task import AgentType

logger = logging.getLogger(__name__)


class RouteResult(BaseModel):
    """Result of routing a business request to an AI teammate."""
    selected_agent: Optional[AgentType] = None
    confidence: float = Field(ge=0.0, le=1.0, description="Routing confidence score")
    task_category: str = Field(description="Category of business request")
    explanation: str = Field(description="Concise justification for routing decision")
    is_ambiguous: bool = False
    clarification_prompt: Optional[str] = None


class AgentRouter:
    """Routes business requests to specialized AI teammates with ambiguity detection."""

    def __init__(self, llm_provider: Optional[BaseLLMProvider] = None):
        self.llm = llm_provider or get_llm_provider()
        self._agents: Dict[AgentType, BaseAgent] = {
            AgentType.SUPPORT: SupportAgent(),
            AgentType.SALES: SalesAgent(),
            AgentType.OPERATIONS: OperationsAgent(),
        }

    def get_agent(self, agent_type: AgentType) -> BaseAgent:
        """Fetch agent instance by AgentType."""
        return self._agents[agent_type]

    def get_agent_by_id(self, agent_id: str) -> Optional[BaseAgent]:
        """Fetch agent instance by string ID."""
        cleaned = agent_id.strip().lower()
        for agent_type, agent in self._agents.items():
            if agent_type.value == cleaned:
                return agent
        return None

    def list_all_agents(self) -> List[BaseAgent]:
        """Return list of all registered teammates."""
        return list(self._agents.values())

    async def determine_route(
        self,
        user_request: str,
        explicit_agent: Optional[str] = None,
    ) -> RouteResult:
        """Comprehensive routing analysis returning structured RouteResult."""
        req_clean = user_request.strip()

        # 1. Handle empty or clearly ambiguous / uninformative inputs
        if not req_clean:
            return RouteResult(
                selected_agent=None,
                confidence=0.0,
                task_category="empty",
                explanation="No business request provided.",
                is_ambiguous=True,
                clarification_prompt="Please provide a description of the business task to be handled.",
            )

        # Gibberish or single word vague commands
        vague_patterns = ["asdf", "test", "help", "do something", "hello", "hey", "xyz", "what"]
        if req_clean.lower() in vague_patterns or (len(req_clean) < 5 and not any(k in req_clean.lower() for k in ["sku", "crm", "rfp"])):
            return RouteResult(
                selected_agent=None,
                confidence=0.1,
                task_category="ambiguous",
                explanation="Request lacks sufficient business context to determine an appropriate teammate.",
                is_ambiguous=True,
                clarification_prompt=(
                    "Your request is ambiguous. Please clarify whether this relates to "
                    "Customer Support (tickets, refunds), Sales (pricing, leads), or Operations (inventory, reports)."
                ),
            )

        # 2. Check explicit agent selection
        if explicit_agent:
            cleaned = explicit_agent.strip().lower()
            target_type = None
            for at in AgentType:
                if at.value == cleaned:
                    target_type = at
                    break

            if target_type:
                return RouteResult(
                    selected_agent=target_type,
                    confidence=1.0,
                    task_category=f"{target_type.value}_explicit",
                    explanation=f"Explicitly assigned to {self._agents[target_type].name} by user directive.",
                    is_ambiguous=False,
                )
            else:
                logger.warning("Unrecognized explicit agent '%s', falling back to automatic routing.", explicit_agent)

        # 3. Automatic routing via LLM
        system_prompt = (
            "You are the AgentX Intelligent Router. Analyze the business request and route it to ONE teammate:\n"
            "- 'support': customer complaints, refunds, order tracking, payment disputes, support tickets\n"
            "- 'sales': leads, commercial quotes, enterprise contracts, pricing inquiries, CRM follow-ups\n"
            "- 'operations': warehouse inventory, reports, data audits, logistics, stock anomalies\n\n"
            "If the request is totally incomprehensible or not a business task, respond with category 'ambiguous'.\n"
            "Output strictly in format:\n"
            "CATEGORY: <support|sales|operations|ambiguous>\n"
            "CONFIDENCE: <0.0 to 1.0>\n"
            "REASON: <concise 1-sentence explanation>"
        )
        prompt = f"Request: {req_clean}\nRouting:"

        try:
            raw = await self.llm.generate_text(prompt, system_instruction=system_prompt)
            route_res = self._parse_llm_route(raw)
            if route_res:
                return route_res
        except Exception as exc:
            logger.warning("LLM routing failed: %s. Using heuristic classification.", exc)

        # 4. Fallback heuristic classification
        return self._heuristic_route(req_clean)

    async def route(
        self,
        user_request: str,
        explicit_agent: Optional[str] = None,
    ) -> Tuple[AgentType, BaseAgent]:
        """Backward-compatible routing method returning (AgentType, BaseAgent)."""
        result = await self.determine_route(user_request, explicit_agent)
        
        # If ambiguous, default safely to Support for human escalation
        if result.is_ambiguous or not result.selected_agent:
            return AgentType.SUPPORT, self._agents[AgentType.SUPPORT]

        return result.selected_agent, self._agents[result.selected_agent]

    def _parse_llm_route(self, text: str) -> Optional[RouteResult]:
        """Parse structured text output from routing LLM prompt."""
        if not text:
            return None

        cat_match = re.search(r"CATEGORY:\s*([a-zA-Z_]+)", text, re.IGNORECASE)
        conf_match = re.search(r"CONFIDENCE:\s*([0-9\.]+)", text)
        reason_match = re.search(r"REASON:\s*(.+)", text, re.IGNORECASE)

        if cat_match:
            category = cat_match.group(1).strip().lower()
            confidence = float(conf_match.group(1)) if conf_match else 0.85
            confidence = min(max(confidence, 0.0), 1.0)
            reason = reason_match.group(1).strip() if reason_match else "Categorized via LLM analysis."

            if category == "ambiguous":
                return RouteResult(
                    selected_agent=None,
                    confidence=confidence,
                    task_category="ambiguous",
                    explanation=reason,
                    is_ambiguous=True,
                    clarification_prompt="Request could not be definitively routed. Please provide more context.",
                )

            for agent_type in AgentType:
                if agent_type.value == category:
                    return RouteResult(
                        selected_agent=agent_type,
                        confidence=confidence,
                        task_category=category,
                        explanation=reason,
                        is_ambiguous=False,
                    )

        return None

    def _heuristic_route(self, request: str) -> RouteResult:
        """Deterministic keyword heuristic for fallback routing."""
        req_lower = request.lower()

        sales_keywords = ["price", "pricing", "discount", "quote", "sales", "demo", "lead", "prospect", "contract", "enterprise"]
        ops_keywords = ["inventory", "stock", "warehouse", "logistics", "supply", "shipping", "operations", "report", "data", "audit"]
        support_keywords = ["refund", "ticket", "complaint", "order", "payment", "customer", "issue", "delay", "cancel"]

        sales_score = sum(1 for k in sales_keywords if k in req_lower)
        ops_score = sum(1 for k in ops_keywords if k in req_lower)
        support_score = sum(1 for k in support_keywords if k in req_lower)

        if sales_score > ops_score and sales_score > support_score:
            return RouteResult(
                selected_agent=AgentType.SALES,
                confidence=0.88,
                task_category="sales",
                explanation="Request contains commercial, lead, or pricing terminology.",
            )
        elif ops_score > sales_score and ops_score > support_score:
            return RouteResult(
                selected_agent=AgentType.OPERATIONS,
                confidence=0.88,
                task_category="operations",
                explanation="Request contains logistics, warehouse, data audit, or inventory terminology.",
            )
        elif support_score > 0:
            return RouteResult(
                selected_agent=AgentType.SUPPORT,
                confidence=0.88,
                task_category="support",
                explanation="Request contains customer support, ticket, or refund resolution terminology.",
            )

        # Default fallback
        return RouteResult(
            selected_agent=AgentType.SUPPORT,
            confidence=0.65,
            task_category="support_default",
            explanation="Defaulted to Support Teammate for triage.",
        )
