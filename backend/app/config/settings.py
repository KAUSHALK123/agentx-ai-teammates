from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env file."""
    
    app_name: str = "AgentX — Autonomous AI Teammates"
    app_version: str = "0.1.0"
    agentx_env: str = "development"
    app_env: str = "development"
    
    # Server configuration
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173"
    
    # LLM configuration (Grok / xAI & Gemini)
    llm_provider: str = "grok"
    grok_api_key: Optional[str] = None
    xai_api_key: Optional[str] = None
    grok_model: str = "grok-2-latest"
    grok_base_url: str = "https://api.x.ai/v1"
    
    gemini_api_key: Optional[str] = None
    gemini_model: str = "gemini-2.5-flash"
    
    # Supabase configuration (for future phases)
    supabase_url: Optional[str] = None
    supabase_key: Optional[str] = None

    # n8n Workflow Integration
    n8n_base_url: str = "http://localhost:32768"
    n8n_api_key: Optional[str] = None
    n8n_timeout_seconds: float = 30.0
    n8n_webhook_timeout_seconds: float = 30.0
    n8n_retry_attempts: int = 2

    # Workflow Webhook URLs (Individually Configurable)
    n8n_sales_webhook_url: Optional[str] = None
    n8n_support_webhook_url: Optional[str] = None
    n8n_operations_webhook_url: Optional[str] = None
    n8n_gmail_webhook_url: Optional[str] = None
    n8n_crm_webhook_url: Optional[str] = None
    n8n_support_case_webhook_url: Optional[str] = None

    # Cognee Cloud / Local Knowledge Layer
    cognee_service_url: Optional[str] = None
    cognee_api_key: Optional[str] = None
    cognee_dataset_name: str = "agentx_business_knowledge"
    cognee_mode: str = "cloud"
    cognee_timeout_seconds: float = 15.0

    @property
    def get_timeout(self) -> float:
        return self.n8n_timeout_seconds if self.n8n_timeout_seconds is not None else self.n8n_webhook_timeout_seconds

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


@lru_cache()
def get_settings() -> Settings:
    """Return cached application settings instance."""
    return Settings()
