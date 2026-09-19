import logging
from typing import Any, Dict, Optional
from app.knowledge.service import KnowledgeService, get_knowledge_service
from app.tools.base import BaseTool, ToolResult

logger = logging.getLogger(__name__)


class LookupKnowledgeTool(BaseTool):
    """Tool that queries the AgentX Cognee Knowledge Base for business policies and rules."""
    tool_id: str = "lookup_knowledge"
    name: str = "Knowledge Base Search"
    description: str = (
        "Search the AgentX business knowledge graph (powered by Cognee) for refund policies, "
        "support SLAs, return rules, product catalog specs, and operational procedures."
    )
    category: str = "support"
    is_write: bool = False
    input_schema: Dict[str, Any] = {
        "type": "object",
        "required": ["query"],
        "properties": {
            "query": {"type": "string", "description": "Search query or question (e.g. 'refund policy for delayed orders')"},
            "limit": {"type": "integer", "description": "Maximum chunks to retrieve (default: 3)"},
        },
    }
    output_schema: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "chunks_found": {"type": "integer"},
            "knowledge_used": {"type": "array"},
            "results": {"type": "array"},
        },
    }

    def __init__(self, knowledge_service: Optional[KnowledgeService] = None):
        self.knowledge_service = knowledge_service or get_knowledge_service()

    async def execute(self, **kwargs: Any) -> ToolResult:
        query = kwargs.get("query")
        limit = kwargs.get("limit") or 3

        if not query:
            return ToolResult(
                success=False,
                tool_id=self.tool_id,
                error="Missing required 'query' parameter",
                message="Cannot search knowledge base without a query string",
            )

        try:
            search_res = await self.knowledge_service.search(query=str(query), limit=int(limit))
            knowledge_used = [
                {
                    "source": chunk.source,
                    "content": chunk.content,
                    "score": chunk.score,
                }
                for chunk in search_res.results
            ]

            return ToolResult(
                success=True,
                tool_id=self.tool_id,
                data={
                    "query": search_res.query,
                    "chunks_found": len(search_res.results),
                    "knowledge_used": knowledge_used,
                    "provider": search_res.provider,
                },
                error=search_res.error,
                message=f"Retrieved {len(search_res.results)} knowledge chunks for '{query}'",
            )
        except Exception as exc:
            logger.exception("LookupKnowledgeTool execution error: %s", exc)
            return ToolResult(
                success=False,
                tool_id=self.tool_id,
                error=str(exc),
                message="Unexpected error searching knowledge base",
            )
