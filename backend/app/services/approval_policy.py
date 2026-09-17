import logging
import re
from typing import Any, Dict, Optional
from pydantic import BaseModel
from app.models.approval import RiskLevel

logger = logging.getLogger(__name__)


class PolicyDecision(BaseModel):
    """Result of evaluating an action against the approval policy."""
    approval_required: bool
    risk_level: RiskLevel
    reason: str


class ApprovalPolicyService:
    """Centralized, deterministic approval policy evaluating action safety and human-in-the-loop triggers."""

    # High-risk keywords signaling externally visible, financial, or destructive side-effects
    HIGH_RISK_ACTION_PATTERNS = [
        (r"\b(send|dispatch|publish)\b.*\b(email|message|sms|notification|response|reply)\b", "External communication requires supervisor approval"),
        (r"\b(refund|reimburse|payout|compensat|chargeback)\b", "Financial transaction or refund requires authorized approval"),
        (r"\b(delete|destroy|purge|drop)\b", "Destructive data deletion requires human confirmation"),
        (r"\b(discount|credit|write-?off)\b", "Financial adjustment or write-off requires management review"),
        (r"\b(cancel|void)\b.*\b(order|contract|subscription)\b", "Order or contract cancellation requires human review"),
    ]

    # Explicit high-risk tool IDs (for future email/refund/payment tools)
    HIGH_RISK_TOOLS = {
        "send_email",
        "send_sms",
        "issue_refund",
        "cancel_order",
        "delete_record",
        "apply_discount",
    }

    def evaluate(
        self,
        agent_id: str,
        tool_id: Optional[str],
        action: str,
        parameters: Optional[Dict[str, Any]] = None,
        explicit_risk: Optional[RiskLevel] = None,
    ) -> PolicyDecision:
        """Deterministically assess if an action requires human approval before execution."""
        params = parameters or {}
        action_text = action.strip()
        action_lower = action_text.lower()

        # 1. Check explicit override if provided
        if explicit_risk == RiskLevel.HIGH:
            return PolicyDecision(
                approval_required=True,
                risk_level=RiskLevel.HIGH,
                reason="Explicitly classified as high-risk action",
            )

        # 2. Check high-risk tools
        if tool_id and tool_id.lower() in self.HIGH_RISK_TOOLS:
            return PolicyDecision(
                approval_required=True,
                risk_level=RiskLevel.HIGH,
                reason=f"Tool '{tool_id}' performs externally visible or financial mutations",
            )

        # 3. Check action text against regex patterns
        for pattern, reason in self.HIGH_RISK_ACTION_PATTERNS:
            if re.search(pattern, action_lower):
                return PolicyDecision(
                    approval_required=True,
                    risk_level=RiskLevel.HIGH,
                    reason=reason,
                )

        # 4. Check parameter-specific high-risk conditions
        # e.g., large refunds, high discounts, or external recipients
        if "recipient" in params or "to_email" in params:
            return PolicyDecision(
                approval_required=True,
                risk_level=RiskLevel.HIGH,
                reason="Direct outbound communication to external recipient requires human approval",
            )

        if "amount" in params and isinstance(params["amount"], (int, float)) and params["amount"] > 1000.0:
            if "refund" in action_lower or "adjust" in action_lower:
                return PolicyDecision(
                    approval_required=True,
                    risk_level=RiskLevel.HIGH,
                    reason=f"Financial action exceeds autonomous threshold (amount: {params['amount']})",
                )

        # Default to LOW risk for read-only / internal analysis actions
        return PolicyDecision(
            approval_required=False,
            risk_level=RiskLevel.LOW,
            reason="Low-risk internal action operates autonomously without approval",
        )

    def evaluate_action(
        self,
        agent: str,
        tool_id: Optional[str],
        action: str,
        proposed_input: Optional[Dict[str, Any]] = None,
        explicit_risk: Optional[RiskLevel] = None,
    ) -> PolicyDecision:
        """Alias for evaluate matching action classification interface."""
        return self.evaluate(
            agent_id=agent,
            tool_id=tool_id,
            action=action,
            parameters=proposed_input,
            explicit_risk=explicit_risk,
        )


_global_approval_policy: Optional[ApprovalPolicyService] = None


def get_approval_policy() -> ApprovalPolicyService:
    """Return singleton instance of approval policy service."""
    global _global_approval_policy
    if _global_approval_policy is None:
        _global_approval_policy = ApprovalPolicyService()
    return _global_approval_policy
