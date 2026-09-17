from fastapi import APIRouter
from app.api.v1.health import router as health_router
from app.api.v1.tasks import router as tasks_router

api_v1_router = APIRouter()
api_v1_router.include_router(health_router, tags=["Health"])
api_v1_router.include_router(tasks_router, prefix="/tasks", tags=["Tasks"])

__all__ = ["api_v1_router"]
