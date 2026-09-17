from typing import Any, Dict, Optional


class SupportTicketService:
    """Service simulating external Customer Support System / Helpdesk API."""

    _mock_tickets = {
        "1234": {"ticket_id": "1234", "customer": "Acme Corp", "status": "open", "issue": "Order delay", "priority": "high"},
        "5678": {"ticket_id": "5678", "customer": "Globex Inc", "status": "resolved", "issue": "Billing question", "priority": "medium"},
    }

    @classmethod
    async def find_ticket(cls, query: str) -> Optional[Dict[str, Any]]:
        """Look up support ticket by ID or customer reference."""
        for tid, data in cls._mock_tickets.items():
            if tid in query or data["customer"].lower() in query.lower():
                return data
        return {"ticket_id": "GEN-999", "customer": "Customer", "status": "active", "query": query}


class SalesCRMService:
    """Service simulating external Sales CRM / Lead Management System."""

    @classmethod
    async def qualify_lead(cls, company_or_inquiry: str) -> Dict[str, Any]:
        """Evaluate business inquiry for deal size and tier eligibility."""
        is_enterprise = any(k in company_or_inquiry.lower() for k in ["enterprise", "volume", "custom", "organization"])
        tier = "Enterprise Tier" if is_enterprise else "Standard Growth"
        return {
            "inquiry": company_or_inquiry,
            "qualified": True,
            "tier": tier,
            "recommended_plan": "Enterprise Annual" if is_enterprise else "Pro Monthly",
            "discount_eligible": is_enterprise,
        }


class OperationsInventoryService:
    """Service simulating Warehouse & Logistics ERP."""

    _mock_inventory = {
        "SKU-101": {"sku": "SKU-101", "name": "AI Edge Gateway", "stock": 450, "location": "Warehouse A"},
        "SKU-202": {"sku": "SKU-202", "name": "Telemetry Node", "stock": 12, "location": "Warehouse B (Low Stock)"},
    }

    @classmethod
    async def check_inventory(cls, query: str) -> Dict[str, Any]:
        """Query inventory level from ERP."""
        for sku, info in cls._mock_inventory.items():
            if sku.lower() in query.lower() or info["name"].lower() in query.lower():
                return info
        return {
            "sku": "SKU-DEFAULT",
            "name": "General Catalog Item",
            "stock": 100,
            "status": "In Stock",
            "location": "Central Fulfillment",
        }
