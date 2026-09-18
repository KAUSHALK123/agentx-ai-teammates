import logging
from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException, status
from app.models.support import SupportIntent
from app.schemas.support import SupportAnalyzeRequest, SupportAnalyzeResponse
from app.services.data_service import get_data_service, normalize_customer_id
from app.services.support_analyzer import SupportAnalyzer

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/analyze",
    response_model=SupportAnalyzeResponse,
    summary="Analyze customer message, complaint, or review",
)
async def analyze_support_request(request: SupportAnalyzeRequest) -> SupportAnalyzeResponse:
    """Analyze customer message or review for intent, sentiment, severity, context, and recommended action."""
    msg_clean = request.message.strip()
    if not msg_clean:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Message content cannot be empty.",
        )

    ds = get_data_service()
    customer_context: Optional[Dict[str, Any]] = None

    # Customer ID extraction or request parameter
    cid = request.customer_id
    if not cid:
        entities = SupportAnalyzer.extract_entities(msg_clean)
        cid = entities.get("customer_id")

    if cid:
        normalized_cid = normalize_customer_id(cid)
        cust = await ds.get_customer(normalized_cid)
        if cust:
            orders = await ds.get_orders_for_customer(normalized_cid)
            customer_context = {
                "customer": cust.model_dump(),
                "orders_count": len(orders),
                "recent_orders": [o.model_dump() for o in orders],
            }

    # If message is identified as review or feedback
    if any(k in msg_clean.lower() for k in ["review", "stars", "rated", "rating", "experience with"]):
        review_analysis = SupportAnalyzer.analyze_review(msg_clean, customer_id=cid)
        rec_action = f"Execute strategy: {review_analysis.recommended_strategy.value}"
        return SupportAnalyzeResponse(
            intent=review_analysis.intent,
            confidence=0.94,
            sentiment=review_analysis.sentiment,
            severity=review_analysis.severity,
            customer_context=customer_context,
            recommended_action=rec_action,
            recommended_strategy=review_analysis.recommended_strategy,
            response_options=review_analysis.available_options,
            draft_response=review_analysis.draft_response,
            approval_required=review_analysis.approval_required,
            explanation=f"Analyzed customer review: sentiment={review_analysis.sentiment.value}, strategy={review_analysis.recommended_strategy.value}",
        )

    # Standard customer support message analysis
    classification = SupportAnalyzer.classify_intent(msg_clean)
    
    # Recommended action & approval requirement
    if classification.intent == SupportIntent.REFUND_REQUEST:
        rec_action = "Investigate transaction discrepancy and issue refund upon human authorization"
        approval_required = True
    elif classification.intent in [SupportIntent.DELAYED_ORDER, SupportIntent.ORDER_ISSUE]:
        rec_action = "Retrieve fulfillment tracking, investigate carrier status, and synthesize customer update"
        approval_required = False
    elif classification.intent in [SupportIntent.PAYMENT_ISSUE, SupportIntent.TRANSACTION_ISSUE]:
        rec_action = "Inspect payment settlement, verify order mismatch, and formulate resolution"
        approval_required = False
    elif classification.intent == SupportIntent.ESCALATION:
        rec_action = "Escalate high-severity issue to human supervisor"
        approval_required = False
    else:
        rec_action = "Investigate customer profile and provide resolution"
        approval_required = False

    options = [
        "Apologize + Provide Update",
        "Offer Compensation",
        "Request More Information",
        "Escalate",
        "Custom Response",
    ]

    return SupportAnalyzeResponse(
        intent=classification.intent,
        confidence=classification.confidence,
        sentiment=SupportAnalyzer.analyze_sentiment(msg_clean),
        severity=classification.severity,
        customer_context=customer_context,
        recommended_action=rec_action,
        response_options=options,
        approval_required=approval_required,
        explanation=classification.explanation,
    )
