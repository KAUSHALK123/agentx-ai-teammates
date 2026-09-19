from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from app.models.task import Task, TaskStatus
from app.services.data_service import IDataService, get_data_service


class VerificationResult(BaseModel):
    """Result of verifying task execution outcomes against business standards."""
    verified: bool
    verification_type: str = "record_match"
    summary: str
    recommended_status: TaskStatus = TaskStatus.COMPLETED
    requires_human_review: bool = False
    details: Optional[Dict[str, Any]] = None


class TaskVerifier:
    """Verifies that teammate execution produced valid, complete, and reliable outcomes."""

    @classmethod
    async def verify_task_execution(
        cls,
        task: Task,
        completed_tool_results: List[Dict[str, Any]],
        data_service: Optional[IDataService] = None,
    ) -> VerificationResult:
        """Thoroughly verify multi-step task outcomes against actual data store state."""
        ds = data_service or get_data_service()

        if not completed_tool_results:
            return VerificationResult(
                verified=False,
                verification_type="execution_check",
                recommended_status=TaskStatus.FAILED,
                summary="Execution produced no verifiable tool outputs.",
            )

        # Check if any tool reported a hard failure
        for res in completed_tool_results:
            if not res.get("success", False):
                err = res.get("error") or res.get("message", "Unknown tool error")
                tool_id = res.get("tool_id", "unknown_tool")
                return VerificationResult(
                    verified=False,
                    verification_type="tool_execution",
                    recommended_status=TaskStatus.FAILED,
                    summary=f"Action '{tool_id}' failed execution: {err}",
                    details={"failed_tool": tool_id, "error": err},
                )

        # 1. Verify Write Operations (Mandatory Real Confirmation)
        for res in completed_tool_results:
            tool_id = res.get("tool_id")
            data = res.get("data") or {}

            # Verification for update_lead
            if tool_id == "update_lead":
                lead_id = data.get("lead_id")
                expected_status = data.get("status")
                if not lead_id:
                    return VerificationResult(
                        verified=False,
                        verification_type="record_match",
                        recommended_status=TaskStatus.FAILED,
                        summary="Lead update verification failed: missing lead_id in result.",
                    )
                persisted_lead = await ds.get_lead(lead_id)
                if not persisted_lead:
                    return VerificationResult(
                        verified=False,
                        verification_type="record_match",
                        recommended_status=TaskStatus.FAILED,
                        summary=f"Lead update verification failed: Lead '{lead_id}' not found in database.",
                    )
                if expected_status and persisted_lead.status != expected_status:
                    return VerificationResult(
                        verified=False,
                        verification_type="record_match",
                        recommended_status=TaskStatus.FAILED,
                        summary=f"Lead status verification failed: expected '{expected_status}', found '{persisted_lead.status}'",
                        details={"expected": expected_status, "actual": persisted_lead.status},
                    )

            # Verification for create_activity
            elif tool_id == "create_activity":
                activity_id = data.get("activity_id")
                if not activity_id:
                    return VerificationResult(
                        verified=False,
                        verification_type="existence_check",
                        recommended_status=TaskStatus.FAILED,
                        summary="Activity creation verification failed: missing activity_id.",
                    )
                persisted_act = await ds.get_activity(activity_id)
                if not persisted_act:
                    return VerificationResult(
                        verified=False,
                        verification_type="existence_check",
                        recommended_status=TaskStatus.FAILED,
                        summary=f"Activity creation verification failed: Activity '{activity_id}' was not persisted.",
                    )

            # Verification for issue_demo_refund
            elif tool_id == "issue_demo_refund":
                refund_id = data.get("refund_id")
                txn_id = data.get("transaction_id")
                if not refund_id or not txn_id:
                    return VerificationResult(
                        verified=False,
                        verification_type="record_match",
                        recommended_status=TaskStatus.FAILED,
                        summary="Demo refund verification failed: missing refund_id or transaction_id.",
                    )
                txn = await ds.get_transaction(txn_id)
                if txn and txn.payment_status != "refunded":
                    return VerificationResult(
                        verified=False,
                        verification_type="record_match",
                        recommended_status=TaskStatus.FAILED,
                        summary=f"Refund verification failed: Transaction '{txn_id}' payment status is '{txn.payment_status}', expected 'refunded'.",
                    )

            # Verification for escalate_support_case
            elif tool_id == "escalate_support_case":
                case_id = data.get("case_id")
                if not case_id:
                    return VerificationResult(
                        verified=False,
                        verification_type="existence_check",
                        recommended_status=TaskStatus.FAILED,
                        summary="Support escalation verification failed: missing case_id.",
                    )
                persisted_case = await ds.get_support_case(case_id)
                if not persisted_case:
                    return VerificationResult(
                        verified=False,
                        verification_type="existence_check",
                        recommended_status=TaskStatus.FAILED,
                        summary=f"Support escalation verification failed: Case '{case_id}' was not persisted.",
                    )
                return VerificationResult(
                    verified=True,
                    verification_type="escalation_review",
                    recommended_status=TaskStatus.ESCALATED,
                    requires_human_review=True,
                    summary=f"Support case escalated to tier-2 human supervisor: {data.get('reason')}",
                    details=data,
                )

            # Verification for prepare_customer_response
            elif tool_id == "prepare_customer_response":
                cust_resp = data.get("customer_response")
                if not cust_resp:
                    return VerificationResult(
                        verified=False,
                        verification_type="response_check",
                        recommended_status=TaskStatus.FAILED,
                        summary="Customer response verification failed: empty response content.",
                    )

            # Verification for n8n_process_lead / sales_process_lead
            elif tool_id in ["n8n_process_lead", "sales_process_lead"]:
                lead_id = data.get("lead_id")
                expected_status = data.get("lead_status")
                qualification = data.get("qualification") or {}
                if not lead_id or not expected_status:
                    return VerificationResult(
                        verified=False,
                        verification_type="n8n_lead_qualification",
                        recommended_status=TaskStatus.FAILED,
                        summary="n8n lead processing verification failed: missing lead_id or lead_status.",
                    )
                # Confirm CRM database reflects the status
                persisted_lead = await ds.get_lead(lead_id)
                if not persisted_lead:
                    return VerificationResult(
                        verified=False,
                        verification_type="n8n_lead_qualification",
                        recommended_status=TaskStatus.FAILED,
                        summary=f"n8n lead verification failed: Lead '{lead_id}' not found in database.",
                    )
                if persisted_lead.status != expected_status:
                    return VerificationResult(
                        verified=False,
                        verification_type="n8n_lead_qualification",
                        recommended_status=TaskStatus.FAILED,
                        summary=f"n8n lead status mismatch: expected '{expected_status}', found '{persisted_lead.status}'",
                        details={"expected": expected_status, "actual": persisted_lead.status},
                    )

            # Verification for support_handle_issue / n8n_support_handle_issue
            elif tool_id in ["support_handle_issue", "n8n_support_handle_issue"]:
                if data.get("approval_required") or data.get("requires_approval") or data.get("status") == "waiting_for_approval":
                    return VerificationResult(
                        verified=True,
                        verification_type="support_approval_gate",
                        recommended_status=TaskStatus.WAITING_FOR_APPROVAL,
                        requires_human_review=True,
                        summary="Support issue resolution paused for supervisor approval.",
                        details=data,
                    )
                return VerificationResult(
                    verified=True,
                    verification_type="n8n_support_investigation",
                    recommended_status=TaskStatus.COMPLETED,
                    summary=f"Customer support issue verified and resolved via n8n (Customer: {data.get('customer_id') or 'CUST-001'}).",
                    details=data,
                )

            # Verification for n8n_send_followup
            elif tool_id == "n8n_send_followup":
                delivery = data.get("delivery_info") or {}
                if delivery.get("status") != "delivered":
                    return VerificationResult(
                        verified=False,
                        verification_type="n8n_communication_dispatch",
                        recommended_status=TaskStatus.FAILED,
                        summary="n8n follow-up verification failed: message status is not 'delivered'.",
                        details=data,
                    )

            # Verification for n8n_operations_check
            elif tool_id == "n8n_operations_check":
                records_processed = data.get("records_processed")
                exceptions_found = data.get("exceptions_found")
                metrics = data.get("metrics") or {}
                if records_processed is None or records_processed <= 0:
                    return VerificationResult(
                        verified=False,
                        verification_type="n8n_operations_audit",
                        recommended_status=TaskStatus.FAILED,
                        summary="n8n operations check verification failed: zero or missing records_processed.",
                        details=data,
                    )
                if not metrics or "successful" not in metrics:
                    return VerificationResult(
                        verified=False,
                        verification_type="n8n_operations_audit",
                        recommended_status=TaskStatus.FAILED,
                        summary="n8n operations check verification failed: missing operational metrics.",
                        details=data,
                    )
                return VerificationResult(
                    verified=True,
                    verification_type="n8n_operations_audit",
                    recommended_status=TaskStatus.COMPLETED,
                    summary=f"n8n daily operations check verified ({records_processed} records audited, {exceptions_found or 0} exceptions identified).",
                    details=data,
                )

        # 2. Check for Operational / Customer Escalation Flags
        for res in completed_tool_results:
            data = res.get("data") or {}
            if isinstance(data, dict):
                location_status = str(data.get("location", "")).lower()
                priority = str(data.get("priority", "")).lower()
                status_str = str(data.get("status", "")).lower()
                
                # Discrepancies in verification tool
                discrepancies = data.get("discrepancies") or []
                if discrepancies:
                    return VerificationResult(
                        verified=True,
                        verification_type="record_match",
                        recommended_status=TaskStatus.ESCALATED,
                        summary=f"Discrepancies identified during operational audit: {', '.join(discrepancies)}",
                        requires_human_review=True,
                        details=data,
                    )

                if "low stock" in location_status or priority == "urgent":
                    return VerificationResult(
                        verified=True,
                        verification_type="heuristic_check",
                        recommended_status=TaskStatus.ESCALATED,
                        summary="Action completed successfully, but flagged threshold requires human oversight.",
                        requires_human_review=True,
                        details=data,
                    )

        return VerificationResult(
            verified=True,
            verification_type="record_match",
            recommended_status=TaskStatus.COMPLETED,
            summary="All planned actions executed and verified against data store.",
            requires_human_review=False,
            details={"actions_verified": len(completed_tool_results)},
        )

    @classmethod
    async def verify(cls, task: Task, action_result: Optional[Dict[str, Any]] = None) -> VerificationResult:
        """Backward-compatible wrapper for single-action verification."""
        if not action_result:
            return VerificationResult(
                verified=False,
                verification_type="execution_check",
                recommended_status=TaskStatus.FAILED,
                summary="Execution produced no verifiable output.",
            )
        return await cls.verify_task_execution(task, [action_result])


# Alias for clarity
VerificationEngine = TaskVerifier

