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
        """Check availability of the local or cloud n8n instance."""
        headers = {}
        if self.api_key:
            headers["X-N8N-API-KEY"] = self.api_key

        test_urls = [f"{self.base_url}/healthz", f"{self.base_url}/"]
        sales_url = self.resolve_webhook_url("sales")
        if sales_url:
            test_urls.append(sales_url)

        for target_url in test_urls:
            try:
                async with httpx.AsyncClient(timeout=3.0) as client:
                    res = await client.get(target_url, headers=headers)
                    if res.status_code in (200, 401, 404, 405):
                        return {
                            "available": True,
                            "base_url": self.base_url,
                            "configured": True,
                            "status_code": res.status_code,
                            "registered_workflows": list(APPROVED_N8N_WORKFLOWS.keys()),
                        }
            except Exception:
                pass

        if "localhost" in self.base_url or "127.0.0.1" in self.base_url:
            alt = await self._discover_fallback_port()
            if alt:
                return await self.check_health()

        return {
            "available": False,
            "base_url": self.base_url,
            "configured": True,
            "error": f"Unable to reach n8n at {self.base_url}",
            "registered_workflows": list(APPROVED_N8N_WORKFLOWS.keys()),
        }

    def resolve_webhook_url(self, workflow_type: str) -> Optional[str]:
        """Centrally map workflow type to environment variable URL or default base endpoint."""
        settings = get_settings()
        wf = workflow_type.lower().strip()
        if wf in ("sales", "sales_process_lead", "01_sales_process_lead"):
            return settings.n8n_sales_webhook_url or f"{self.base_url}/webhook/agentx-sales-process-lead"
        elif wf in ("support", "support_handle_issue", "02_support_handle_issue"):
            return settings.n8n_support_webhook_url or f"{self.base_url}/webhook/agentx-support-handle-issue"
        elif wf in ("operations", "operations_daily_business_check", "operations_daily_check", "03_operations_daily_check"):
            return settings.n8n_operations_webhook_url or f"{self.base_url}/webhook/agentx-operations-daily-check"
        elif wf in ("gmail", "gmail_send_approved_email", "04_gmail_send_approved_email", "sales_send_followup", "send_customer_email", "agentx-gmail-send-approved-email"):
            return settings.n8n_gmail_webhook_url or f"{self.base_url}/webhook/agentx-gmail-send-approved-email"
        elif wf in ("crm", "crm_lead_actions", "05_crm_lead_actions", "update_lead", "agentx-crm-lead-actions"):
            return settings.n8n_crm_webhook_url or f"{self.base_url}/webhook/agentx-crm-lead-actions"
        elif wf in ("support_case", "support_case_actions", "06_support_case_actions", "escalate_case", "update_support_case", "agentx-support-case-actions"):
            return settings.n8n_support_case_webhook_url or f"{self.base_url}/webhook/agentx-support-case-actions"
        return None

    async def execute_workflow(self, workflow_type: str, payload: Any) -> N8nExecutionResult:
        """Generic reusable workflow execution interface.
        
        Supports execute_workflow(workflow_type, payload).
        Maps workflow types centrally via env variables (N8N_SALES_WEBHOOK_URL, N8N_SUPPORT_WEBHOOK_URL, N8N_OPERATIONS_WEBHOOK_URL).
        Returns normalized N8nExecutionResult with structured error codes on failure.
        """
        body = payload.model_dump() if hasattr(payload, "model_dump") else (payload if isinstance(payload, dict) else {})
        if not body.get("action"):
            body["action"] = body.get("requested_action") or "process_lead"
        if not body.get("requested_action"):
            body["requested_action"] = body.get("action")
        if not body.get("check_type"):
            body["check_type"] = "daily"

        # Idempotency Check
        task_id = body.get("task_id") or "task_general"
        cache_key = body.get("idempotency_key") or f"{task_id}:{workflow_type}"
        async with self._lock:
            if cache_key in self._idempotency_cache:
                logger.info("Returning cached result for idempotency key: %s", cache_key)
                return self._idempotency_cache[cache_key]

        webhook_url = self.resolve_webhook_url(workflow_type)
        if not webhook_url:
            code = "N8N_CONFIG_MISSING"
            msg = f"Webhook URL or configuration missing for workflow type '{workflow_type}'"
            return N8nExecutionResult(
                success=False,
                status="failed",
                workflow=workflow_type,
                task_id=task_id,
                error=f"{code}: {msg}",
                error_details={"code": code, "message": msg},
            )

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-N8N-API-KEY"] = self.api_key

        last_code = "N8N_EXECUTION_FAILED"
        last_message = "Workflow execution failed after retries"
        attempt = 0

        while attempt <= self.retry_attempts:
            attempt += 1
            try:
                logger.info(
                    "Executing n8n workflow_type '%s' at '%s' (attempt %d/%d)",
                    workflow_type,
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
                        code = "N8N_MALFORMED_RESPONSE"
                        msg = f"Invalid JSON response: {json_err}"
                        return N8nExecutionResult(
                            success=False,
                            status="failed",
                            workflow=workflow_type,
                            task_id=task_id,
                            error=f"{code}: {msg}",
                            error_details={"code": code, "message": msg},
                        )

                    # Handle array wrapper if returned by n8n
                    data = raw_data[0] if isinstance(raw_data, list) and raw_data else raw_data
                    if not isinstance(data, dict):
                        code = "N8N_MALFORMED_RESPONSE"
                        msg = "Expected dictionary response structure from n8n"
                        return N8nExecutionResult(
                            success=False,
                            status="failed",
                            workflow=workflow_type,
                            task_id=task_id,
                            error=f"{code}: {msg}",
                            error_details={"code": code, "message": msg},
                        )

                    success = bool(data.get("success", True))
                    status = data.get("status", "completed" if success else "failed")
                    approval_required = bool(data.get("approval_required") or data.get("requires_approval") or data.get("requires_human_review"))
                    
                    err_str: Optional[str] = None
                    err_dict: Optional[Dict[str, Any]] = None
                    if not success:
                        raw_err = data.get("error")
                        if isinstance(raw_err, dict):
                            err_str = f"{raw_err.get('code', 'N8N_EXECUTION_FAILED')}: {raw_err.get('message', 'Workflow failed')}"
                            err_dict = raw_err
                        else:
                            err_str = f"N8N_EXECUTION_FAILED: {raw_err or 'Workflow failed'}"
                            err_dict = {"code": "N8N_EXECUTION_FAILED", "message": str(raw_err or "Workflow failed")}

                    result = N8nExecutionResult(
                        success=success,
                        status=status,
                        workflow=str(data.get("workflow", workflow_type)),
                        task_id=data.get("task_id", task_id),
                        lead_id=data.get("lead_id", body.get("lead_id")),
                        customer_id=data.get("customer_id", body.get("customer_id")),
                        order_id=data.get("order_id", body.get("order_id")),
                        approval_required=approval_required,
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
                        lead=data.get("lead"),
                        issue=data.get("issue"),
                        result=data.get("result"),
                        error=err_str,
                        error_details=err_dict,
                        timestamp=data.get("timestamp"),
                    )

                    # Cache successful result for idempotency
                    if success:
                        async with self._lock:
                            self._idempotency_cache[cache_key] = result

                    return result

                elif response.status_code == 404:
                    last_code = "N8N_EXECUTION_FAILED"
                    last_message = f"Webhook endpoint not registered or inactive (HTTP 404) at {webhook_url}"
                    logger.warning("n8n returned 404 for %s", webhook_url)
                    break
                else:
                    last_code = "N8N_HTTP_ERROR"
                    last_message = f"n8n returned HTTP {response.status_code}: {response.text[:200]}"
                    logger.warning("n8n execution failed with HTTP %d: %s", response.status_code, response.text[:200])

            except httpx.ConnectError as conn_err:
                last_code = "N8N_UNAVAILABLE"
                last_message = f"Connection refused to n8n at {webhook_url}"
                logger.warning("n8n connect error on attempt %d: %s", attempt, conn_err)
                if "localhost" in self.base_url or "127.0.0.1" in self.base_url:
                    alt = await self._discover_fallback_port()
                    if alt:
                        webhook_url = self.resolve_webhook_url(workflow_type) or webhook_url

            except httpx.TimeoutException as time_err:
                last_code = "N8N_TIMEOUT"
                last_message = f"n8n request timed out after {self.timeout}s"
                logger.warning("n8n timeout on attempt %d: %s", attempt, time_err)

            except Exception as exc:
                last_code = "N8N_EXECUTION_FAILED"
                last_message = f"Unexpected error during n8n execution: {exc}"
                logger.exception("Unexpected error executing n8n workflow %s: %s", workflow_type, exc)

            if attempt <= self.retry_attempts:
                await asyncio.sleep(0.5 * attempt)

        return N8nExecutionResult(
            success=False,
            status="failed",
            workflow=workflow_type,
            task_id=task_id,
            lead_id=body.get("lead_id"),
            customer_id=body.get("customer_id"),
            order_id=body.get("order_id"),
            error=f"{last_code}: {last_message}",
            error_details={"code": last_code, "message": last_message},
        )

    async def invoke_workflow(self, payload: N8nInvocationPayload) -> N8nExecutionResult:
        """Invoke an approved n8n webhook workflow with security, idempotency, and retries."""
        workflow_id = payload.workflow_id
        
        # 1. Whitelist Verification
        wf_def = get_n8n_workflow_definition(workflow_id)
        if not wf_def:
            logger.error("Attempted invocation of unapproved workflow: %s", workflow_id)
            return N8nExecutionResult(
                success=False,
                status="failed",
                workflow=workflow_id,
                task_id=payload.task_id,
                lead_id=payload.lead_id,
                error="N8N_VALIDATION_ERROR: Workflow is not in approved registry",
                error_details={"code": "N8N_VALIDATION_ERROR", "message": "Workflow is not in approved registry"},
            )

        # 2. Agent Authorization Check
        allowed_agents = [a.strip().lower() for a in wf_def.allowed_agent.split(",")]
        if payload.agent_id.lower() not in allowed_agents:
            logger.error(
                "Agent '%s' is not authorized to invoke workflow '%s' (allowed: '%s')",
                payload.agent_id,
                workflow_id,
                wf_def.allowed_agent,
            )
            return N8nExecutionResult(
                success=False,
                status="failed",
                workflow=workflow_id,
                task_id=payload.task_id,
                lead_id=payload.lead_id,
                error=f"N8N_VALIDATION_ERROR: Agent '{payload.agent_id}' unauthorized for workflow '{workflow_id}'",
                error_details={"code": "N8N_VALIDATION_ERROR", "message": f"Agent '{payload.agent_id}' unauthorized for workflow '{workflow_id}'"},
            )

        # 3. Use generic execute_workflow implementation
        return await self.execute_workflow(workflow_id, payload)


_n8n_provider: Optional[N8nToolProvider] = None


def get_n8n_provider() -> N8nToolProvider:
    """Singleton getter for N8nToolProvider."""
    global _n8n_provider
    if _n8n_provider is None:
        _n8n_provider = N8nToolProvider()
    return _n8n_provider
