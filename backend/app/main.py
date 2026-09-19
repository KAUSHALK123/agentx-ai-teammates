import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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
from app.api.v1 import api_v1_router
from app.config.settings import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("agentx")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle hook for startup and shutdown logging."""
    logger.info("Initializing AgentX Core Backend...")
    yield
    logger.info("Shutting down AgentX Core Backend...")


settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Autonomous AI Teammates for Business — Human-in-the-Loop Approval",
    lifespan=lifespan,
)

# CORS middleware
_cors_origins = [orig.strip() for orig in settings.cors_origins.split(",") if orig.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins if _cors_origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount direct endpoints for root contract
app.include_router(health_router, tags=["Health"])
app.include_router(workspaces_router, prefix="/workspaces", tags=["Workspaces"])
app.include_router(tasks_router, prefix="/tasks", tags=["Tasks"])
app.include_router(agents_router, prefix="/agents", tags=["Agents"])
app.include_router(tools_router, prefix="/tools", tags=["Tools"])
app.include_router(approvals_router, prefix="/approvals", tags=["Approvals"])
app.include_router(support_router, prefix="/support", tags=["Support"])
app.include_router(integrations_router, prefix="/integrations", tags=["Integrations"])
app.include_router(inputs_router, prefix="/inputs", tags=["Inputs"])
app.include_router(knowledge_router, prefix="/knowledge", tags=["Knowledge"])

# Also mount under /api/v1 prefix
app.include_router(api_v1_router, prefix="/api/v1")



@app.get("/", tags=["Root"])
async def root():
    """Service landing endpoint with API metadata."""
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "status": "operational",
        "docs_url": "/docs",
        "health_url": "/health",
        "n8n_health_url": "/health/n8n",
        "tasks_url": "/tasks",
        "agents_url": "/agents",
        "tools_url": "/tools",
        "approvals_url": "/approvals",
        "inputs_url": "/inputs",
        "plan_url": "/tasks/plan",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
    )
