import abc
import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
try:
    import cognee
except ImportError:
    cognee = None

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
    """Cognee Cloud implementation of the knowledge engine provider."""

    def __init__(
        self,
        dataset_name: Optional[str] = None,
        service_url: Optional[str] = None,
        api_key: Optional[str] = None,
        mode: Optional[str] = None,
    ):
        from app.config.settings import get_settings
        settings = get_settings()
        self.dataset_name = dataset_name or settings.cognee_dataset_name
        self.service_url = service_url or settings.cognee_service_url
        self.api_key = api_key or settings.cognee_api_key
        self.mode = mode or settings.cognee_mode or "cloud"
        self._connected = False
        self._connection_error: Optional[str] = None

    async def _ensure_connected(self) -> bool:
        """Connect the Cognee SDK to Cognee Cloud instance if configured, or use local embedded engine."""
        if self._connected:
            return True

        # In cloud mode or auto mode with credentials, connect to Cognee Cloud
        if (self.mode == "cloud" or self.mode == "auto") and (self.service_url or self.api_key):
            try:
                logger.info("Connecting to Cognee Cloud at %s (dataset: %s)...", self.service_url, self.dataset_name)
                await cognee.serve(url=self.service_url, api_key=self.api_key)
                self._connected = True
                self._connection_error = None
                return True
            except Exception as exc:
                self._connection_error = f"Failed to connect to Cognee Cloud: {exc}"
                logger.error("Cognee Cloud connection failure: %s", exc)
                if self.mode == "cloud":
                    return False

        if self.mode == "cloud" and not self.service_url and not self.api_key:
            self._connection_error = "Cognee Cloud credentials missing (COGNEE_SERVICE_URL / COGNEE_API_KEY)."
            logger.warning(self._connection_error)
            return False

        # In auto/local fallback mode
        self._connected = True
        return True

    async def check_health(self) -> Dict[str, Any]:
        """Verify Cognee availability without exposing secrets."""
        version = getattr(cognee, "__version__", "1.6.0")
        is_cloud = bool(self.service_url or self.api_key or self.mode == "cloud")
        base_status = {
            "provider": "cognee",
            "mode": "cloud" if is_cloud else "local",
            "dataset": self.dataset_name,
            "version": str(version),
        }

        if self.mode == "cloud" and not self.service_url and not self.api_key:
            return {
                **base_status,
                "available": False,
                "error": "Cognee Cloud credentials not configured. Please set COGNEE_SERVICE_URL and COGNEE_API_KEY in .env",
            }

        try:
            connected = await self._ensure_connected()
            if not connected:
                return {
                    **base_status,
                    "available": False,
                    "error": self._connection_error or "Unable to reach Cognee Cloud instance",
                }

            return {
                **base_status,
                "available": True,
                "status_details": "Connected to Cognee Cloud" if is_cloud else "Running embedded Cognee knowledge engine",
            }
        except Exception as exc:
            return {
                **base_status,
                "available": False,
                "error": f"Cognee Cloud health check failed: {exc}",
            }

    async def search(self, query: str, limit: int = 5) -> KnowledgeSearchResult:
        """Retrieve relevant knowledge chunks from Cognee Cloud."""
        if not query or not query.strip():
            return KnowledgeSearchResult(
                query=query,
                results=[],
                available=True,
                provider="cognee",
            )

        connected = await self._ensure_connected()
        if not connected:
            return KnowledgeSearchResult(
                query=query,
                results=[],
                available=False,
                provider="cognee",
                error=self._connection_error or "Cognee Cloud unavailable",
            )

        try:
            # Query Cognee Cloud using SearchType.CHUNKS
            raw_results = await cognee.search(query.strip(), cognee.SearchType.CHUNKS)
            chunks: List[KnowledgeChunk] = []

            if isinstance(raw_results, list):
                for item in raw_results:
                    if len(chunks) >= limit:
                        break

                    if isinstance(item, dict):
                        sub_results = item.get("search_result")
                        if isinstance(sub_results, list) and sub_results:
                            for sub in sub_results:
                                if len(chunks) >= limit:
                                    break
                                if isinstance(sub, dict):
                                    text = sub.get("text") or sub.get("content") or str(sub)
                                    doc = sub.get("file_path") or sub.get("source") or sub.get("id") or "cloud_document"
                                    score = sub.get("score")
                                    chunks.append(
                                        KnowledgeChunk(
                                            content=str(text),
                                            source=str(doc),
                                            score=float(score) if score is not None else None,
                                            metadata={"dataset": self.dataset_name, "cloud": True},
                                        )
                                    )
                        else:
                            text = item.get("text") or item.get("content") or str(item)
                            chunks.append(KnowledgeChunk(content=str(text), source="cognee_cloud_document", metadata={"dataset": self.dataset_name, "cloud": True}))
                    else:
                        text_attr = getattr(item, "text", str(item))
                        chunks.append(KnowledgeChunk(content=str(text_attr), source="cognee_cloud_document", metadata={"dataset": self.dataset_name, "cloud": True}))

            return KnowledgeSearchResult(
                query=query,
                results=chunks[:limit],
                available=True,
                provider="cognee",
            )
        except Exception as exc:
            logger.warning("Cognee Cloud search failed: %s", exc)
            return KnowledgeSearchResult(
                query=query,
                results=[],
                available=False,
                provider="cognee",
                error=f"Cognee Cloud retrieval error: {exc}",
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
