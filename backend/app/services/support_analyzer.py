import logging
import re
from typing import Any, Dict, List, Optional
from app.models.support import (
    CustomerReviewAnalysis,
    ResponseStrategy,
    ReviewSentiment,
    SupportIntent,
    SupportIntentClassification,
    SupportSeverity,
)
from app.services.data_service import (
    normalize_customer_id,
    normalize_order_id,
    normalize_transaction_id,
)

logger = logging.getLogger(__name__)


class SupportAnalyzer:
    """Intelligent, deterministic analysis engine for customer support inquiries and reviews."""

    # Keywords for intent detection
    INTENT_KEYWORDS = {
        SupportIntent.REFUND_REQUEST: [
            "refund", "reimburse", "money back", "chargeback", "payout", "failed transaction",
            "refund customer", "process refund", "issue refund"
        ],
        SupportIntent.DELAYED_ORDER: [
            "delayed", "delay", "hasn't arrived", "not arrived", "has not arrived",
            "late delivery", "still waiting", "where is my order", "order not received",
            "tracking says", "taking too long", "delivery overdue"
        ],
        SupportIntent.PAYMENT_ISSUE: [
            "payment went through", "payment status", "paid but", "debited", "double charge",
            "charged twice", "charged but", "payment deducted", "payment mismatch",
            "money deducted", "gateway error", "payment pending"
        ],
        SupportIntent.TRANSACTION_ISSUE: [
            "transaction failed", "transaction mismatch", "txn failed", "transaction error",
            "transaction settlement", "transaction dispute"
        ],
        SupportIntent.RETURN_REQUEST: [
            "return", "exchange", "send back", "return item", "return order", "pickup return"
        ],
        SupportIntent.CUSTOMER_REVIEW: [
            "review", "stars", "rating", "rated", "feedback", "customer review",
            "1 star", "2 star", "5 star"
        ],
        SupportIntent.ESCALATION: [
            "escalate", "escalation", "supervisor", "manager", "legal", "lawyer",
            "lawsuit", "police", "consumer court", "urgent attention"
        ],
        SupportIntent.CUSTOMER_COMPLAINT: [
            "complaint", "terrible", "horrible", "awful", "worst", "unacceptable",
            "poor service", "pathetic", "frustrated", "disgusted", "cheat"
        ],
        SupportIntent.ORDER_ISSUE: [
            "order", "order status", "damaged", "broken", "wrong item", "missing item",
            "package opened", "order inquiry"
        ],
    }

    # Sentiment indicators
    POSITIVE_WORDS = ["great", "excellent", "awesome", "good", "satisfied", "happy", "loved", "fast", "helpful"]
    NEGATIVE_WORDS = [
        "terrible", "bad", "horrible", "worst", "awful", "unacceptable", "delay", "delayed",
        "failed", "broken", "scam", "useless", "poor", "frustrated", "disappointed", "never"
    ]

    @classmethod
    def extract_entities(cls, text: str) -> Dict[str, Any]:
        """Extract customer, order, and transaction tokens from text."""
        entities: Dict[str, Any] = {}

        # Customer ID
        cust_match = re.search(r"\b(?:CUST-?|C)0*(\d+)\b", text, re.IGNORECASE)
        if cust_match:
            entities["customer_id"] = normalize_customer_id(cust_match.group(0))

        # Order ID
        ord_match = re.search(r"\b(?:ORD-?|O)0*(\d+)\b", text, re.IGNORECASE)
        if ord_match:
            entities["order_id"] = normalize_order_id(ord_match.group(0))

        # Transaction ID
        txn_match = re.search(r"\b(?:TXN-?|T)0*(\d+)\b", text, re.IGNORECASE)
        if txn_match:
            entities["transaction_id"] = normalize_transaction_id(txn_match.group(0))

        # Financial amount (e.g. INR 2499, $500, Rs. 14500, 14500)
        amt_match = re.search(r"(?:rs\.?|inr|\$)?\s*(\d+(?:\.\d{2})?)\b", text, re.IGNORECASE)
        if amt_match:
            val = float(amt_match.group(1))
            if val > 100:  # avoid small integers like step counts
                entities["amount"] = val

        return entities

    @classmethod
    def classify_severity(
        cls,
        text: str,
        entities: Optional[Dict[str, Any]] = None,
        intent: Optional[SupportIntent] = None,
    ) -> SupportSeverity:
        """Classify severity explainably based on financial impact, risk keywords, and sentiment."""
        text_lower = text.lower()
        ents = entities or {}

        # 1. Critical triggers: legal, regulatory, security, fraud, or high-value monetary disputes
        critical_keywords = ["legal", "lawyer", "lawsuit", "court", "police", "fraud", "scam", "unauthorized", "stolen"]
        if any(w in text_lower for w in critical_keywords):
            return SupportSeverity.CRITICAL

        amount = ents.get("amount", 0.0)
        if amount >= 20000.0:
            return SupportSeverity.CRITICAL

        # 2. High triggers: financial refunds, payment failures, intense anger, large amount
        high_keywords = [
            "refund", "failed transaction", "charged twice", "double charge", "money lost",
            "cheat", "unacceptable", "furious", "severe", "escalate immediately"
        ]
        if any(w in text_lower for w in high_keywords) or intent == SupportIntent.REFUND_REQUEST:
            return SupportSeverity.HIGH

        if amount >= 5000.0 or intent == SupportIntent.PAYMENT_ISSUE:
            return SupportSeverity.HIGH

        # 3. Medium triggers: delayed orders, mismatched status, standard complaints, returns
        medium_keywords = ["delayed", "late", "pending", "not arrived", "return", "broken", "complaint"]
        if any(w in text_lower for w in medium_keywords) or intent in [
            SupportIntent.DELAYED_ORDER,
            SupportIntent.ORDER_ISSUE,
            SupportIntent.RETURN_REQUEST,
            SupportIntent.CUSTOMER_COMPLAINT,
        ]:
            return SupportSeverity.MEDIUM

        # 4. Low triggers: general question, status check, positive/neutral
        return SupportSeverity.LOW

    @classmethod
    def classify_intent(cls, text: str) -> SupportIntentClassification:
        """Deterministically and accurately classify user request into a support intent."""
        text_lower = text.lower().strip()
        entities = cls.extract_entities(text)

        # Check keyword matches with precedence
        detected_intent = SupportIntent.GENERAL_SUPPORT_QUESTION
        max_score = 0

        # Prioritize explicit review keywords
        if any(k in text_lower for k in ["review", "rated", "stars", "rating"]):
            detected_intent = SupportIntent.CUSTOMER_REVIEW
            max_score = 10
        else:
            # Check other intents
            intent_order = [
                SupportIntent.REFUND_REQUEST,
                SupportIntent.PAYMENT_ISSUE,
                SupportIntent.DELAYED_ORDER,
                SupportIntent.TRANSACTION_ISSUE,
                SupportIntent.RETURN_REQUEST,
                SupportIntent.ESCALATION,
                SupportIntent.CUSTOMER_COMPLAINT,
                SupportIntent.ORDER_ISSUE,
            ]
            for intent in intent_order:
                keywords = cls.INTENT_KEYWORDS.get(intent, [])
                score = sum(2 if k in text_lower and len(k.split()) > 1 else 1 for k in keywords if k in text_lower)
                if score > max_score:
                    max_score = score
                    detected_intent = intent

        confidence = 0.95 if max_score >= 2 else (0.88 if max_score == 1 else 0.75)
        severity = cls.classify_severity(text, entities, detected_intent)

        explanation = (
            f"Classified as {detected_intent.value} based on contextual indicators: "
            f"severity={severity.value}, extracted_entities={list(entities.keys())}"
        )

        return SupportIntentClassification(
            intent=detected_intent,
            confidence=confidence,
            severity=severity,
            explanation=explanation,
            extracted_entities=entities,
        )

    @classmethod
    def analyze_sentiment(cls, text: str) -> ReviewSentiment:
        """Classify sentiment of customer feedback or review."""
        text_lower = text.lower()
        pos_count = sum(1 for w in cls.POSITIVE_WORDS if w in text_lower)
        neg_count = sum(1 for w in cls.NEGATIVE_WORDS if w in text_lower)

        if neg_count > pos_count:
            return ReviewSentiment.NEGATIVE
        elif pos_count > neg_count:
            return ReviewSentiment.POSITIVE
        return ReviewSentiment.NEUTRAL

    @classmethod
    def analyze_review(
        cls,
        review_text: str,
        customer_id: Optional[str] = None,
    ) -> CustomerReviewAnalysis:
        """Process customer review, determining sentiment, strategy, and draft response."""
        sentiment = cls.analyze_sentiment(review_text)
        entities = cls.extract_entities(review_text)
        if customer_id:
            entities["customer_id"] = normalize_customer_id(customer_id)

        intent_res = cls.classify_intent(review_text)
        # If intent classified generally as customer review, identify specific sub-intent
        sub_intent = intent_res.intent
        if sub_intent == SupportIntent.CUSTOMER_REVIEW:
            if "delay" in review_text.lower() or "not arrived" in review_text.lower() or "late" in review_text.lower():
                sub_intent = SupportIntent.DELAYED_ORDER
            elif "refund" in review_text.lower() or "money" in review_text.lower():
                sub_intent = SupportIntent.REFUND_REQUEST
            elif "pay" in review_text.lower() or "charged" in review_text.lower():
                sub_intent = SupportIntent.PAYMENT_ISSUE
            else:
                sub_intent = SupportIntent.CUSTOMER_COMPLAINT

        severity = cls.classify_severity(review_text, entities, sub_intent)

        # Standard strategy options
        available_options = [
            ResponseStrategy.APOLOGIZE_AND_UPDATE.value,
            ResponseStrategy.OFFER_COMPENSATION.value,
            ResponseStrategy.REQUEST_MORE_INFO.value,
            ResponseStrategy.ESCALATE.value,
            ResponseStrategy.CUSTOM_RESPONSE.value,
        ]

        # Determine strategy
        if severity == SupportSeverity.CRITICAL or "legal" in review_text.lower():
            strategy = ResponseStrategy.ESCALATE
            draft = (
                "Dear Customer, we sincerely apologize for your experience. Your case has been escalated "
                "to our senior management team for immediate investigation. A supervisor will contact you directly."
            )
        elif sub_intent in [SupportIntent.REFUND_REQUEST, SupportIntent.PAYMENT_ISSUE] or severity == SupportSeverity.HIGH:
            strategy = ResponseStrategy.OFFER_COMPENSATION
            draft = (
                "Dear Customer, we apologize for the payment inconvenience you encountered. "
                "We have initiated an investigation into your transaction and are processing compensation/refund options."
            )
        elif sub_intent == SupportIntent.DELAYED_ORDER:
            strategy = ResponseStrategy.APOLOGIZE_AND_UPDATE
            draft = (
                "Dear Customer, we sincerely apologize for the delay in delivering your order. "
                "Our logistics team is actively expediting transit, and you will receive an updated delivery ETA shortly."
            )
        elif not entities.get("order_id") and not entities.get("customer_id"):
            strategy = ResponseStrategy.REQUEST_MORE_INFO
            draft = (
                "Dear Customer, thank you for your feedback. To help us investigate and resolve this promptly, "
                "could you please share your Order ID or registered contact details?"
            )
        else:
            strategy = ResponseStrategy.CUSTOM_RESPONSE
            draft = (
                "Dear Customer, thank you for sharing your feedback with AgentX. "
                "We take customer satisfaction seriously and are addressing your concerns."
            )

        return CustomerReviewAnalysis(
            sentiment=sentiment,
            intent=sub_intent,
            severity=severity,
            recommended_strategy=strategy,
            available_options=available_options,
            draft_response=draft,
            approval_required=True,  # External communication always requires approval
            context_found=entities,
        )
