from typing import Any, Dict
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.knowledge.service import KnowledgeSearchResult, get_knowledge_service

router = APIRouter()


class KnowledgeSearchRequest(BaseModel):
    """Payload for knowledge base search query."""
    query: str = Field(..., description="Search query string")
    limit: int = Field(default=5, ge=1, le=20, description="Max chunks to return")


@router.post("/search", response_model=KnowledgeSearchResult, summary="Search Knowledge Base")
async def search_knowledge(payload: KnowledgeSearchRequest) -> KnowledgeSearchResult:
    """Search Cognee Knowledge engine for relevant policy chunks."""
    if not payload.query or not payload.query.strip():
        raise HTTPException(status_code=400, detail="Query parameter cannot be empty")

    service = get_knowledge_service()
    return await service.search(query=payload.query.strip(), limit=payload.limit)


@router.get("/status", summary="Check Knowledge Integration Status")
async def get_knowledge_status() -> Dict[str, Any]:
    """Check availability of Cognee knowledge provider."""
    service = get_knowledge_service()
    return await service.check_health()
