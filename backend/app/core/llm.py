from abc import ABC, abstractmethod
import logging
from typing import Optional
import httpx
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


class GrokLLMProvider(BaseLLMProvider):
    """Grok (xAI) & GroqCloud LLM provider implementation (OpenAI-compatible /chat/completions API)."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        settings = get_settings()
        self.api_key = api_key or settings.grok_api_key or settings.xai_api_key
        
        # Auto-detect GroqCloud (gsk_...) vs xAI Grok (xai-...)
        if self.api_key and self.api_key.startswith("gsk_"):
            self.base_url = (base_url or "https://api.groq.com/openai/v1").rstrip("/")
            self.model_name = model_name or (
                settings.grok_model if settings.grok_model and "grok" not in settings.grok_model.lower()
                else "openai/gpt-oss-120b"
            )
        else:
            self.base_url = (base_url or settings.grok_base_url or "https://api.x.ai/v1").rstrip("/")
            self.model_name = model_name or settings.grok_model or "grok-2-latest"

    async def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
    ) -> str:
        """Generate response via Grok API (xAI), or gracefully fallback."""
        if self.api_key and self.api_key != "your_grok_api_key_here":
            try:
                messages = []
                if system_instruction:
                    messages.append({"role": "system", "content": system_instruction})
                messages.append({"role": "user", "content": prompt})

                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                }
                payload = {
                    "model": self.model_name,
                    "messages": messages,
                    "temperature": 0.2,
                }

                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.post(
                        f"{self.base_url}/chat/completions",
                        headers=headers,
                        json=payload,
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        choices = data.get("choices", [])
                        if choices and "message" in choices[0]:
                            return choices[0]["message"].get("content", "").strip()
                    else:
                        logger.warning("Grok API returned status %s: %s", resp.status_code, resp.text)
            except Exception as exc:
                logger.error("Grok API call failed: %s. Reverting to fallback.", exc)

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
    """Factory function returning the configured LLM provider (Grok / Gemini / Mock)."""
    settings = get_settings()
    if settings.llm_provider.lower() == "gemini":
        return GeminiLLMProvider()
    # Default to Grok (xAI) provider
    return GrokLLMProvider()
