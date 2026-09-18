from typing import Any, Dict
from fastapi import APIRouter
from app.services.n8n_provider import get_n8n_provider

router = APIRouter()


@router.get("/n8n/status", summary="Check n8n Integration Status")
async def get_n8n_status() -> Dict[str, Any]:
    """Check connectivity to the n8n automation engine and list approved workflows."""
    provider = get_n8n_provider()
    return await provider.check_health()
