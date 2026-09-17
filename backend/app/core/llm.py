from abc import ABC, abstractmethod
import logging
from typing import Optional
from app.config.settings import get_settings

logger = logging.getLogger(__name__)


class BaseLLMProvider(ABC):
    """Abstract Base Class for LLM providers."""

    @abstractmethod
    async def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
    ) -> str:
        """Generate text completion from prompt."""
        pass


class GeminiLLMProvider(BaseLLMProvider):
    """Google Gemini LLM provider implementation with fallback resilience."""

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        settings = get_settings()
        self.api_key = api_key or settings.gemini_api_key
        self.model_name = model_name or settings.gemini_model
        self._client = None
        self._initialize_client()

    def _initialize_client(self) -> None:
        """Initialize Google GenAI client if API key is present."""
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            logger.info("Gemini API key not configured. Operating in simulated fallback mode.")
            return

        try:
            from google import genai
            self._client = genai.Client(api_key=self.api_key)
            logger.info("Initialized Google GenAI client with model: %s", self.model_name)
        except Exception as exc:
            logger.warning("Could not initialize Google GenAI client: %s. Using fallback mode.", exc)
            self._client = None

    async def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
    ) -> str:
        """Generate response via Gemini API, or gracefully fallback."""
        if self._client:
            try:
                # Async call or sync in executor
                response = self._client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config={"system_instruction": system_instruction} if system_instruction else None,
                )
                if response and response.text:
                    return response.text.strip()
            except Exception as exc:
                logger.error("Gemini API call failed: %s. Reverting to fallback.", exc)

        return self._generate_fallback(prompt, system_instruction)

    def _generate_fallback(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        """Deterministic fallback generation when API key is not present or offline."""
        prompt_lower = prompt.lower()
        if "classify" in prompt_lower or "router" in prompt_lower:
            if any(k in prompt_lower for k in ["refund", "ticket", "issue", "complaint", "customer", "support"]):
                return "support"
            elif any(k in prompt_lower for k in ["price", "pricing", "discount", "lead", "enterprise", "quote", "sales"]):
                return "sales"
            elif any(k in prompt_lower for k in ["inventory", "stock", "warehouse", "logistics", "operations", "shipment"]):
                return "operations"
            return "support"

        return f"Processed request: {prompt[:100]}"


class MockLLMProvider(BaseLLMProvider):
    """Mock LLM Provider for unit testing."""

    def __init__(self, preset_response: str = "support"):
        self.preset_response = preset_response

    async def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
    ) -> str:
        return self.preset_response


def get_llm_provider() -> BaseLLMProvider:
    """Factory function returning the configured LLM provider."""
    return GeminiLLMProvider()
