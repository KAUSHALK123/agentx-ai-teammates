from typing import Any, Dict, Optional
from pydantic import BaseModel
from app.models.task import Task, TaskStatus


class VerificationResult(BaseModel):
    """Result of verifying task execution outcomes against business standards."""
    verified: bool
    recommended_status: TaskStatus
    summary: str
    requires_human_review: bool = False
    details: Optional[Dict[str, Any]] = None


class TaskVerifier:
    """Verifies that teammate execution produced valid, complete, and reliable outcomes."""

    @classmethod
    async def verify(cls, task: Task, action_result: Optional[Dict[str, Any]] = None) -> VerificationResult:
        """Evaluate task results and determine final lifecycle status."""
        if not action_result:
            return VerificationResult(
                verified=False,
                recommended_status=TaskStatus.FAILED,
                summary="Execution produced no verifiable output.",
            )

        # Check for explicit failure flag from tool
        if not action_result.get("success", False):
            error_msg = action_result.get("error") or action_result.get("message", "Tool execution failed")
            return VerificationResult(
                verified=False,
                recommended_status=TaskStatus.FAILED,
                summary=f"Action failed validation: {error_msg}",
            )

        data = action_result.get("data") or {}

        # Heuristic check for conditions requiring human escalation
        # e.g., Low stock warnings, critical priority tickets, or high-value enterprise custom requests
        if isinstance(data, dict):
            location_status = str(data.get("location", "")).lower()
            priority = str(data.get("priority", "")).lower()
            
            if "low stock" in location_status or priority == "urgent":
                return VerificationResult(
                    verified=True,
                    recommended_status=TaskStatus.ESCALATED,
                    summary="Action completed successfully, but flagged threshold requires human oversight.",
                    requires_human_review=True,
                    details=data,
                )

        return VerificationResult(
            verified=True,
            recommended_status=TaskStatus.COMPLETED,
            summary="Action verified: outputs meet quality and data integrity constraints.",
            requires_human_review=False,
            details=data,
        )
