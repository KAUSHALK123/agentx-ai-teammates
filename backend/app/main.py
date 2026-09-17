import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.health import router as health_router
from app.api.v1.tasks import router as tasks_router
from app.api.v1.agents import router as agents_router
from app.api.v1.tools import router as tools_router
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
    settings = get_settings()
    logger.info("Starting %s (v%s) in %s mode", settings.app_name, settings.app_version, settings.agentx_env)
    yield
    logger.info("Shutting down AgentX backend service.")


settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Autonomous AI Teammates for Business — Tool & Data Layer",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount direct endpoints for root contract
app.include_router(health_router, tags=["Health"])
app.include_router(tasks_router, prefix="/tasks", tags=["Tasks"])
app.include_router(agents_router, prefix="/agents", tags=["Agents"])
app.include_router(tools_router, prefix="/tools", tags=["Tools"])

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
        "tasks_url": "/tasks",
        "agents_url": "/agents",
        "tools_url": "/tools",
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
