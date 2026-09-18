from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env file."""
    
    app_name: str = "AgentX — Autonomous AI Teammates"
    app_version: str = "0.1.0"
    agentx_env: str = "development"
    
    # Server configuration
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173"
    
    # LLM configuration
    gemini_api_key: Optional[str] = None
    gemini_model: str = "gemini-2.5-flash"
    
    # Supabase configuration (for future phases)
    supabase_url: Optional[str] = None
    supabase_key: Optional[str] = None

    # n8n Workflow Integration
    n8n_base_url: str = "http://localhost:32768"
    n8n_api_key: Optional[str] = None
    n8n_webhook_timeout_seconds: float = 10.0
    n8n_retry_attempts: int = 2

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


@lru_cache()
def get_settings() -> Settings:
    """Return cached application settings instance."""
    return Settings()
