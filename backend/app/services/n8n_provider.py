import asyncio
import logging
from typing import Any, Dict, Optional
import httpx
from app.config.settings import get_settings
from app.models.n8n import (
    APPROVED_N8N_WORKFLOWS,
    N8nExecutionResult,
    N8nInvocationPayload,
    get_n8n_workflow_definition,
)

logger = logging.getLogger(__name__)


class N8nToolProvider:
    """Provider responsible for invoking and interacting with n8n workflows.
    
    Acts as the secure bridge between AgentX Tool Layer and n8n Docker instance.
    Enforces workflow whitelist, idempotency caching, structured response parsing,
    and granular error classification.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: Optional[float] = None,
        retry_attempts: Optional[int] = None,
    ):
        settings = get_settings()
        self.base_url = (base_url or settings.n8n_base_url).rstrip("/")
        self.api_key = api_key or settings.n8n_api_key
        self.timeout = timeout if timeout is not None else settings.n8n_webhook_timeout_seconds
        self.retry_attempts = retry_attempts if retry_attempts is not None else settings.n8n_retry_attempts
        
        # Idempotency cache: (task_id, workflow_id) -> N8nExecutionResult
        self._idempotency_cache: Dict[str, N8nExecutionResult] = {}
        self._lock = asyncio.Lock()

    async def _discover_fallback_port(self) -> Optional[str]:
        """Probe common alternative Docker host ports when primary port connection fails."""
        for alt_port in [32770, 32769, 32768, 32771, 32772, 5678]:
            for host in ["127.0.0.1", "localhost"]:
                alt_url = f"http://{host}:{alt_port}"
                if alt_url == self.base_url:
                    continue
                try:
                    async with httpx.AsyncClient(timeout=0.8) as client:
                        res = await client.get(f"{alt_url}/healthz")
                        if res.status_code == 200:
                            logger.info("Auto-discovered active n8n instance at %s (switching from %s)", alt_url, self.base_url)
                            self.base_url = alt_url
                            return alt_url
                except Exception:
                    pass
        return None

    async def check_health(self) -> Dict[str, Any]:
        """Check availability of the local n8n instance."""
        url = f"{self.base_url}/healthz"
        headers = {}
        if self.api_key:
            headers["X-N8N-API-KEY"] = self.api_key

        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                res = await client.get(url, headers=headers)
                available = res.status_code == 200
                return {
                    "available": available,
                    "base_url": self.base_url,
                    "configured": True,
                    "status_code": res.status_code,
                    "registered_workflows": list(APPROVED_N8N_WORKFLOWS.keys()),
                }
        except Exception as exc:
            if "localhost" in self.base_url:
                alt = await self._discover_fallback_port()
                if alt:
                    return await self.check_health()
            logger.warning("n8n health check failed: %s", exc)
            return {
                "available": False,
                "base_url": self.base_url,
                "configured": True,
                "error": str(exc),
                "registered_workflows": list(APPROVED_N8N_WORKFLOWS.keys()),
            }

    async def invoke_workflow(self, payload: N8nInvocationPayload) -> N8nExecutionResult:
        """Invoke an approved n8n webhook workflow with security, idempotency, and retries."""
        workflow_id = payload.workflow_id
        
        # 1. Whitelist Verification
        wf_def = get_n8n_workflow_definition(workflow_id)
        if not wf_def:
            logger.error("Attempted invocation of unapproved workflow: %s", workflow_id)
            return N8nExecutionResult(
                success=False,
                workflow=workflow_id,
                task_id=payload.task_id,
                lead_id=payload.lead_id,
                error="N8N_VALIDATION_ERROR: Workflow is not in approved registry",
            )

        # 2. Agent Authorization Check
        if payload.agent_id != wf_def.allowed_agent:
            logger.error(
                "Agent '%s' is not authorized to invoke workflow '%s' (allowed: '%s')",
                payload.agent_id,
                workflow_id,
                wf_def.allowed_agent,
            )
            return N8nExecutionResult(
                success=False,
                workflow=workflow_id,
                task_id=payload.task_id,
                lead_id=payload.lead_id,
                error=f"N8N_VALIDATION_ERROR: Agent '{payload.agent_id}' unauthorized for workflow '{workflow_id}'",
            )

        # 3. Idempotency Check
        cache_key = payload.idempotency_key or f"{payload.task_id}:{workflow_id}"
        async with self._lock:
            if cache_key in self._idempotency_cache:
                logger.info("Returning cached result for idempotency key: %s", cache_key)
                cached = self._idempotency_cache[cache_key]
                return cached

        # 4. Invoke n8n Webhook
        webhook_url = f"{self.base_url}/webhook/{wf_def.webhook_path}"
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-N8N-API-KEY"] = self.api_key

        body = payload.model_dump()

        last_error: Optional[str] = None
        attempt = 0
        while attempt <= self.retry_attempts:
            attempt += 1
            try:
                logger.info(
                    "Invoking n8n workflow '%s' at '%s' (attempt %d/%d)",
                    workflow_id,
                    webhook_url,
                    attempt,
                    self.retry_attempts + 1,
                )
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(webhook_url, json=body, headers=headers)

                if response.status_code == 200:
                    try:
                        raw_data = response.json()
                    except Exception as json_err:
                        logger.error("Failed to parse n8n response as JSON: %s", json_err)
                        return N8nExecutionResult(
                            success=False,
                            workflow=workflow_id,
                            task_id=payload.task_id,
                            lead_id=payload.lead_id,
                            error=f"N8N_MALFORMED_RESPONSE: {json_err}",
                        )

                    # Handle list of items or single item from n8n
                    data = raw_data[0] if isinstance(raw_data, list) and raw_data else raw_data
                    if not isinstance(data, dict):
                        return N8nExecutionResult(
                            success=False,
                            workflow=workflow_id,
                            task_id=payload.task_id,
                            lead_id=payload.lead_id,
                            error="N8N_MALFORMED_RESPONSE: Expected dictionary response",
                        )

                    # Normalize result fields
                    success = bool(data.get("success", True))
                    result = N8nExecutionResult(
                        success=success,
                        workflow=str(data.get("workflow", workflow_id)),
                        task_id=data.get("task_id", payload.task_id),
                        lead_id=data.get("lead_id", payload.lead_id),
                        lead_status=data.get("lead_status"),
                        qualification=data.get("qualification"),
                        actions=data.get("actions", []),
                        follow_up=data.get("follow_up"),
                        delivery_info=data.get("delivery_info"),
                        records_processed=data.get("records_processed"),
                        exceptions_found=data.get("exceptions_found"),
                        requires_attention=data.get("requires_attention"),
                        metrics=data.get("metrics"),
                        report=data.get("report"),
                        error=data.get("error") if not success else None,
                        timestamp=data.get("timestamp"),
                    )

                    # Cache successful / final result for idempotency
                    async with self._lock:
                        self._idempotency_cache[cache_key] = result

                    return result

                elif response.status_code == 404:
                    last_error = f"N8N_EXECUTION_FAILED: Webhook endpoint not registered or inactive (HTTP 404)"
                    logger.warning("n8n returned 404 for %s", webhook_url)
                    break  # Non-transient 404, don't retry blindly
                else:
                    last_error = f"N8N_EXECUTION_FAILED: n8n returned HTTP {response.status_code}: {response.text[:200]}"
                    logger.warning("n8n invocation failed with code %d: %s", response.status_code, response.text[:200])

            except httpx.ConnectError as conn_err:
                last_error = f"N8N_UNAVAILABLE: Connection refused at {self.base_url}"
                logger.warning("n8n connect error on attempt %d: %s", attempt, conn_err)
                if "localhost" in self.base_url or "127.0.0.1" in self.base_url:
                    alt = await self._discover_fallback_port()
                    if alt:
                        webhook_url = f"{self.base_url}/webhook/{wf_def.webhook_path}"
            except httpx.TimeoutException as time_err:
                last_error = f"N8N_TIMEOUT: Request timed out after {self.timeout}s"
                logger.warning("n8n timeout on attempt %d: %s", attempt, time_err)
            except Exception as exc:
                last_error = f"N8N_EXECUTION_FAILED: Unexpected error: {exc}"
                logger.exception("Unexpected error invoking n8n workflow %s: %s", workflow_id, exc)

            if attempt <= self.retry_attempts:
                await asyncio.sleep(0.5 * attempt)

        return N8nExecutionResult(
            success=False,
            workflow=workflow_id,
            task_id=payload.task_id,
            lead_id=payload.lead_id,
            error=last_error or "N8N_EXECUTION_FAILED: Workflow invocation failed",
        )


_n8n_provider: Optional[N8nToolProvider] = None


def get_n8n_provider() -> N8nToolProvider:
    """Singleton getter for N8nToolProvider."""
    global _n8n_provider
    if _n8n_provider is None:
        _n8n_provider = N8nToolProvider()
    return _n8n_provider
