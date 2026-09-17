import logging
from typing import Dict, Optional, Tuple
from app.agents.base import BaseAgent
from app.agents.support_agent import SupportAgent
from app.agents.sales_agent import SalesAgent
from app.agents.operations_agent import OperationsAgent
from app.core.llm import BaseLLMProvider, get_llm_provider
from app.models.task import AgentType

logger = logging.getLogger(__name__)


class AgentRouter:
    """Routes incoming business tasks to the appropriate specialized AI teammate."""

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

    async def route(
        self,
        user_request: str,
        explicit_agent: Optional[str] = None,
    ) -> Tuple[AgentType, BaseAgent]:
        """Determine the right teammate either via explicit selection or automatic routing."""
        # 1. Check explicit selection
        if explicit_agent:
            cleaned = explicit_agent.strip().lower()
            for agent_type in AgentType:
                if agent_type.value == cleaned:
                    return agent_type, self._agents[agent_type]
            logger.warning(f"Unknown explicit agent '{explicit_agent}', falling back to auto-routing.")

        # 2. Automatic selection via LLM classification
        system_prompt = (
            "You are an AgentX classifier. Classify the user business request into exactly ONE of "
            "the following categories: 'support', 'sales', 'operations'. "
            "Reply with ONLY the single word (lowercase)."
        )
        prompt = f"Request: {user_request}\nClassification:"
        
        try:
            classification = await self.llm.generate_text(prompt, system_instruction=system_prompt)
            classification = classification.strip().lower()
            
            for agent_type in AgentType:
                if agent_type.value in classification:
                    return agent_type, self._agents[agent_type]
        except Exception as exc:
            logger.warning(f"Auto-routing LLM error: {exc}. Using fallback keyword matcher.")

        # 3. Deterministic keyword fallback
        req_lower = user_request.lower()
        if any(w in req_lower for k in ["price", "pricing", "discount", "enterprise", "quote", "sales", "demo", "buy"] for w in [k]):
            return AgentType.SALES, self._agents[AgentType.SALES]
        elif any(w in req_lower for k in ["inventory", "stock", "warehouse", "logistics", "supply", "shipping", "operations"] for w in [k]):
            return AgentType.OPERATIONS, self._agents[AgentType.OPERATIONS]
        
        # Default fallback is Support
        return AgentType.SUPPORT, self._agents[AgentType.SUPPORT]
