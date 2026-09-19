from fastapi import APIRouter
from app.api.v1.health import router as health_router
from app.api.v1.workspaces import router as workspaces_router
from app.api.v1.tasks import router as tasks_router
from app.api.v1.agents import router as agents_router
from app.api.v1.tools import router as tools_router
from app.api.v1.approvals import router as approvals_router
from app.api.v1.support import router as support_router
from app.api.v1.integrations import router as integrations_router
from app.api.v1.inputs import router as inputs_router
from app.api.v1.knowledge import router as knowledge_router

api_v1_router = APIRouter()
api_v1_router.include_router(health_router, tags=["Health"])
api_v1_router.include_router(workspaces_router, prefix="/workspaces", tags=["Workspaces"])
api_v1_router.include_router(tasks_router, prefix="/tasks", tags=["Tasks"])
api_v1_router.include_router(agents_router, prefix="/agents", tags=["Agents"])
api_v1_router.include_router(tools_router, prefix="/tools", tags=["Tools"])
api_v1_router.include_router(approvals_router, prefix="/approvals", tags=["Approvals"])
api_v1_router.include_router(support_router, prefix="/support", tags=["Support"])
api_v1_router.include_router(integrations_router, prefix="/integrations", tags=["Integrations"])
api_v1_router.include_router(inputs_router, prefix="/inputs", tags=["Inputs"])
api_v1_router.include_router(knowledge_router, prefix="/knowledge", tags=["Knowledge"])

__all__ = ["api_v1_router"]

