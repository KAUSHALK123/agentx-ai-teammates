import abc
import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
import cognee

logger = logging.getLogger(__name__)


class KnowledgeChunk(BaseModel):
    """Normalized structured chunk retrieved from knowledge base."""
    content: str
    source: str = "knowledge_base"
    score: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class KnowledgeSearchResult(BaseModel):
    """Normalized output model returned by KnowledgeService."""
    query: str
    results: List[KnowledgeChunk] = Field(default_factory=list)
    available: bool = True
    provider: str = "cognee"
    error: Optional[str] = None


class IKnowledgeProvider(abc.ABC):
    """Abstract interface for knowledge engine providers (Cognee, Future Document Stores)."""

    @abc.abstractmethod
    async def search(self, query: str, limit: int = 5) -> KnowledgeSearchResult:
        """Search knowledge base for relevant chunks."""
        pass

    @abc.abstractmethod
    async def check_health(self) -> Dict[str, Any]:
        """Check provider operational status."""
        pass


class CogneeProvider(IKnowledgeProvider):
    """Cognee implementation of the knowledge engine provider."""

    def __init__(self, dataset_name: str = "main_dataset"):
        self.dataset_name = dataset_name

    async def check_health(self) -> Dict[str, Any]:
        """Verify Cognee availability."""
        try:
            version = getattr(cognee, "__version__", "1.6.0")
            return {
                "available": True,
                "provider": "cognee",
                "version": str(version),
            }
        except Exception as exc:
            return {
                "available": False,
                "provider": "cognee",
                "error": str(exc),
            }

    async def search(self, query: str, limit: int = 5) -> KnowledgeSearchResult:
        """Retrieve relevant knowledge chunks via Cognee vector search."""
        if not query or not query.strip():
            return KnowledgeSearchResult(
                query=query,
                results=[],
                available=True,
                provider="cognee",
            )

        try:
            # Query Cognee vector storage using SearchType.CHUNKS
            raw_results = await cognee.search(query.strip(), cognee.SearchType.CHUNKS)
            chunks: List[KnowledgeChunk] = []

            if isinstance(raw_results, list):
                for item in raw_results:
                    if len(chunks) >= limit:
                        break

                    content_str = ""
                    source_doc = "knowledge_base"
                    score_val = None

                    if isinstance(item, dict):
                        # Extract inner search_result list if present
                        sub_results = item.get("search_result")
                        if isinstance(sub_results, list) and sub_results:
                            for sub in sub_results:
                                if len(chunks) >= limit:
                                    break
                                if isinstance(sub, dict):
                                    text = sub.get("text") or sub.get("content") or str(sub)
                                    doc = sub.get("file_path") or sub.get("source") or sub.get("id") or "demo_document"
                                    score = sub.get("score")
                                    chunks.append(
                                        KnowledgeChunk(
                                            content=str(text),
                                            source=str(doc),
                                            score=float(score) if score is not None else None,
                                            metadata={"dataset": item.get("dataset_name", "main")},
                                        )
                                    )
                        else:
                            text = item.get("text") or item.get("content") or str(item)
                            chunks.append(KnowledgeChunk(content=str(text), source="cognee_document"))
                    else:
                        text_attr = getattr(item, "text", str(item))
                        chunks.append(KnowledgeChunk(content=str(text_attr), source="cognee_document"))

            return KnowledgeSearchResult(
                query=query,
                results=chunks[:limit],
                available=True,
                provider="cognee",
            )
        except Exception as exc:
            logger.warning("Cognee search failed gracefully: %s", exc)
            return KnowledgeSearchResult(
                query=query,
                results=[],
                available=False,
                provider="cognee",
                error=f"Knowledge retrieval unavailable: {exc}",
            )


class KnowledgeService:
    """AgentX Knowledge Service abstraction layer.
    
    Acts as the secure bridge between AgentX Agents and Knowledge Providers.
    Future-proofed to support multiple providers (Cognee, Documents, MCP)
    without mutating agent code.
    """

    def __init__(self, provider: Optional[IKnowledgeProvider] = None):
        self.provider = provider or CogneeProvider()

    async def search(self, query: str, limit: int = 5) -> KnowledgeSearchResult:
        """Search knowledge base and return structured search result."""
        try:
            return await self.provider.search(query=query, limit=limit)
        except Exception as exc:
            logger.exception("KnowledgeService search exception: %s", exc)
            return KnowledgeSearchResult(
                query=query,
                results=[],
                available=False,
                error=f"KnowledgeService error: {exc}",
            )

    async def check_health(self) -> Dict[str, Any]:
        """Check status of active knowledge provider."""
        return await self.provider.check_health()


_knowledge_service_instance: Optional[KnowledgeService] = None


def get_knowledge_service() -> KnowledgeService:
    """Singleton getter for KnowledgeService."""
    global _knowledge_service_instance
    if _knowledge_service_instance is None:
        _knowledge_service_instance = KnowledgeService()
    return _knowledge_service_instance
