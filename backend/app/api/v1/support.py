from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, status
from app.models.support import SupportCaseStatus, SupportIntent
from app.schemas.support import (
    SupportAnalyzeRequest,
    SupportAnalyzeResponse,
    SupportCaseResponse,
    SupportExecuteActionRequest,
    SupportExecuteActionResponse,
)
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


@router.get(
    "/cases",
    response_model=List[SupportCaseResponse],
    summary="List all support cases",
)
async def list_support_cases() -> List[SupportCaseResponse]:
    """Retrieve all support cases tracked in the data service."""
    ds = get_data_service()
    cases = await ds.list_support_cases()
    return [
        SupportCaseResponse(
            case_id=c.case_id,
            task_id=c.task_id,
            customer_id=c.customer_id,
            order_id=c.order_id,
            transaction_id=c.transaction_id,
            intent=c.intent,
            severity=c.severity,
            status=c.status,
            issue_summary=c.issue_summary,
            resolution=c.resolution,
            escalation_reason=c.escalation_reason,
            recommended_human_action=c.recommended_human_action,
            created_at=c.created_at,
            updated_at=c.updated_at,
        )
        for c in cases
    ]


@router.get(
    "/cases/{case_id}",
    response_model=SupportCaseResponse,
    summary="Get support case details",
)
async def get_support_case(case_id: str) -> SupportCaseResponse:
    """Retrieve details for a specific support case."""
    ds = get_data_service()
    case = await ds.get_support_case(case_id)
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Support case '{case_id}' not found.",
        )
    return SupportCaseResponse(
        case_id=case.case_id,
        task_id=case.task_id,
        customer_id=case.customer_id,
        order_id=case.order_id,
        transaction_id=case.transaction_id,
        intent=case.intent,
        severity=case.severity,
        status=case.status,
        issue_summary=case.issue_summary,
        resolution=case.resolution,
        escalation_reason=case.escalation_reason,
        recommended_human_action=case.recommended_human_action,
        created_at=case.created_at,
        updated_at=case.updated_at,
    )


@router.post(
    "/execute-action",
    response_model=SupportExecuteActionResponse,
    summary="Execute selected support response or escalation",
)
async def execute_support_action(request: SupportExecuteActionRequest) -> SupportExecuteActionResponse:
    """Execute a human-selected response or resolution strategy in the support workflow."""
    ds = get_data_service()
    
    # If case exists, update resolution
    if request.case_id:
        case = await ds.get_support_case(request.case_id)
        if case:
            case.resolution = f"Executed: {request.action}. Details: {request.custom_response or 'Standard workflow dispatched.'}"
            if "escalat" in request.action.lower():
                case.status = SupportCaseStatus.ESCALATED
            else:
                case.status = SupportCaseStatus.RESOLVED
            await ds.update_support_case(case)

    # If task exists, update task record
    if request.task_id:
        from app.services.task_store import get_task_store
        tstore = get_task_store()
        task = await tstore.get_task(request.task_id)
        if task:
            task.result = {
                "support_action": request.action,
                "custom_response": request.custom_response,
                "executed_at": datetime.now(timezone.utc).isoformat(),
            }
            await tstore.update_task(task)

    return SupportExecuteActionResponse(
        success=True,
        action=request.action,
        message=f"Successfully executed support action: {request.action}",
        case_id=request.case_id,
        task_id=request.task_id,
        status="EXECUTED",
    )

