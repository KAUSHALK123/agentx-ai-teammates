from datetime import datetime, timezone
from fastapi import APIRouter
from app.config.settings import get_settings
from app.schemas.task import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def get_health() -> HealthResponse:
    """System health check endpoint."""
    settings = get_settings()
    return HealthResponse(
        status="healthy",
        app_name=settings.app_name,
        version=settings.app_version,
        environment=settings.agentx_env,
        timestamp=datetime.now(timezone.utc),
    )


@router.get("/health/n8n")
async def get_n8n_health():
    """Development/health endpoint to verify AgentX -> n8n connectivity."""
    from app.services.n8n_provider import get_n8n_provider
    provider = get_n8n_provider()
    health_info = await provider.check_health()
    reachable = bool(health_info.get("available", False))
    base_url = health_info.get("base_url") or provider.base_url

    if reachable:
        return {
            "status": "ok",
            "n8n": {
                "reachable": True,
                "base_url": base_url,
                "registered_workflows": health_info.get("registered_workflows", []),
            },
        }
    else:
        return {
            "status": "error",
            "n8n": {
                "reachable": False,
                "base_url": base_url,
                "error": health_info.get("error", "n8n service unreachable"),
            },
        }
