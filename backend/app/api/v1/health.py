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
