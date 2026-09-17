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
    
    # LLM configuration
    gemini_api_key: Optional[str] = None
    gemini_model: str = "gemini-2.5-flash"
    
    # Supabase configuration (for future phases)
    supabase_url: Optional[str] = None
    supabase_key: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


@lru_cache()
def get_settings() -> Settings:
    """Return cached application settings instance."""
    return Settings()
