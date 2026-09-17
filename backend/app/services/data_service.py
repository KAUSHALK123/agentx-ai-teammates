import asyncio
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from app.models.business import ActivityRecord, Customer, Lead, OrderTransaction


class IDataService(ABC):
    """Abstract interface defining business data interactions.
    
    Decouples tools from the underlying storage mechanism (Demo in-memory, Supabase, CRM, or APIs).
    """

    @abstractmethod
    async def get_customer(self, customer_id: str) -> Optional[Customer]:
        pass

    @abstractmethod
    async def find_customer(self, query: str) -> Optional[Customer]:
        pass

    @abstractmethod
    async def get_order(self, order_id: str) -> Optional[OrderTransaction]:
        pass

    @abstractmethod
    async def get_orders_for_customer(self, customer_id: str) -> List[OrderTransaction]:
        pass

    @abstractmethod
    async def get_transaction(self, transaction_id: str) -> Optional[OrderTransaction]:
        pass

    @abstractmethod
    async def get_lead(self, lead_id: str) -> Optional[Lead]:
        pass

    @abstractmethod
    async def find_lead(self, query: str) -> Optional[Lead]:
        pass

    @abstractmethod
    async def update_lead(
        self,
        lead_id: str,
        status: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Optional[Lead]:
        pass

    @abstractmethod
    async def get_business_data(self, metric_type: str = "daily_summary") -> Dict[str, Any]:
        pass

    @abstractmethod
    async def verify_record(
        self,
        record_type: str,
        record_id: str,
        expected_fields: Dict[str, Any],
    ) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def create_activity(
        self,
        task_id: str,
        activity_type: str,
        description: str,
    ) -> ActivityRecord:
        pass

    @abstractmethod
    async def get_activity(self, activity_id: str) -> Optional[ActivityRecord]:
        pass

    @abstractmethod
    async def get_activities_for_task(self, task_id: str) -> List[ActivityRecord]:
        pass


class DemoDataService(IDataService):
    """Realistic in-memory business data service for development and testing."""

    def __init__(self):
        self._lock = asyncio.Lock()
        
        # 1. Demo Customers
        self._customers: Dict[str, Customer] = {
            "CUST-001": Customer(
                customer_id="CUST-001",
                name="Alice Sharma",
                email="alice.sharma@example.com",
                phone="+91-9876543210",
                status="active",
            ),
            "CUST-002": Customer(
                customer_id="CUST-002",
                name="Bob Mehta",
                email="bob.mehta@example.com",
                phone="+91-9876543211",
                status="active",
            ),
            "CUST-003": Customer(
                customer_id="CUST-003",
                name="Carol Verma",
                email="carol.verma@example.com",
                phone="+91-9876543212",
                status="active",
            ),
        }

        # 2. Demo Orders and Transactions
        self._orders: Dict[str, OrderTransaction] = {
            "ORD-1001": OrderTransaction(
                order_id="ORD-1001",
                customer_id="CUST-001",
                amount=2499.00,
                status="delivered",
                payment_status="successful",
                transaction_id="TXN-5001",
            ),
            "ORD-1002": OrderTransaction(
                order_id="ORD-1002",
                customer_id="CUST-001",
                amount=14500.00,
                status="pending",
                payment_status="successful",
                transaction_id="TXN-5002",
            ),
            "ORD-1003": OrderTransaction(
                order_id="ORD-1003",
                customer_id="CUST-002",
                amount=890.00,
                status="cancelled",
                payment_status="failed",
                transaction_id="TXN-5003",
            ),
        }

        # 3. Demo Leads
        self._leads: Dict[str, Lead] = {
            "LEAD-001": Lead(
                lead_id="LEAD-001",
                name="Rajesh Khanna",
                email="rajesh@cyberdyne.co.in",
                company="Cyberdyne Tech",
                status="new",
                source="inbound_enterprise",
                notes="Inquired about 500 seat enterprise expansion",
            ),
            "LEAD-002": Lead(
                lead_id="LEAD-002",
                name="Priya Patel",
                email="priya@waynecorp.in",
                company="Wayne India",
                status="contacted",
                source="referral",
                notes="Interested in Q3 logistics automation pilot",
            ),
            "LEAD-101": Lead(
                lead_id="LEAD-101",
                name="Rajesh Khanna",
                email="rajesh@cyberdyne.co.in",
                company="Cyberdyne Tech",
                status="new",
                source="inbound_enterprise",
                notes="Inquired about 500 seat enterprise expansion",
            ),
            "LEAD-102": Lead(
                lead_id="LEAD-102",
                name="Priya Patel",
                email="priya@waynecorp.in",
                company="Wayne India",
                status="contacted",
                source="referral",
                notes="Interested in Q3 logistics automation pilot",
            ),
        }

        # 4. Demo Activities
        self._activities: Dict[str, ActivityRecord] = {}

    async def get_customer(self, customer_id: str) -> Optional[Customer]:
        async with self._lock:
            cust = self._customers.get(customer_id.strip().upper())
            return cust.model_copy() if cust else None

    async def find_customer(self, query: str) -> Optional[Customer]:
        q = query.strip().lower()
        async with self._lock:
            for cust in self._customers.values():
                if (
                    cust.customer_id.lower() == q
                    or q in cust.email.lower()
                    or q in cust.phone.lower()
                    or q in cust.name.lower()
                ):
                    return cust.model_copy()
            return None

    async def get_order(self, order_id: str) -> Optional[OrderTransaction]:
        async with self._lock:
            order = self._orders.get(order_id.strip().upper())
            return order.model_copy() if order else None

    async def get_orders_for_customer(self, customer_id: str) -> List[OrderTransaction]:
        cid = customer_id.strip().upper()
        async with self._lock:
            return [o.model_copy() for o in self._orders.values() if o.customer_id == cid]

    async def get_transaction(self, transaction_id: str) -> Optional[OrderTransaction]:
        tid = transaction_id.strip().upper()
        async with self._lock:
            for order in self._orders.values():
                if order.transaction_id == tid or order.order_id == tid:
                    return order.model_copy()
            return None

    async def get_lead(self, lead_id: str) -> Optional[Lead]:
        async with self._lock:
            lead = self._leads.get(lead_id.strip().upper())
            return lead.model_copy() if lead else None

    async def find_lead(self, query: str) -> Optional[Lead]:
        q = query.strip().lower()
        async with self._lock:
            for lead in self._leads.values():
                if (
                    lead.lead_id.lower() == q
                    or q in lead.company.lower()
                    or q in lead.email.lower()
                    or q in lead.name.lower()
                ):
                    return lead.model_copy()
            return None

    async def update_lead(
        self,
        lead_id: str,
        status: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Optional[Lead]:
        lid = lead_id.strip().upper()
        async with self._lock:
            lead = self._leads.get(lid)
            if not lead:
                return None
            if status:
                lead.status = status
            if notes:
                lead.notes = f"{lead.notes} | {notes}" if lead.notes else notes
            return lead.model_copy()

    async def get_business_data(self, metric_type: str = "daily_summary") -> Dict[str, Any]:
        async with self._lock:
            total_orders = len(self._orders)
            successful_orders = sum(1 for o in self._orders.values() if o.payment_status == "successful")
            revenue = sum(o.amount for o in self._orders.values() if o.payment_status == "successful")
            leads_count = len(self._leads)
            
            return {
                "metric_type": metric_type,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "metrics": {
                    "total_orders": total_orders,
                    "successful_orders": successful_orders,
                    "order_success_rate": round(successful_orders / total_orders, 2) if total_orders else 1.0,
                    "total_revenue": revenue,
                    "active_leads": leads_count,
                    "pending_fulfillment": sum(1 for o in self._orders.values() if o.status == "pending"),
                },
                "status": "operational",
            }

    async def verify_record(
        self,
        record_type: str,
        record_id: str,
        expected_fields: Dict[str, Any],
    ) -> Dict[str, Any]:
        rtype = record_type.strip().lower()
        rid = record_id.strip().upper()

        async with self._lock:
            record_data = None
            if rtype in ["order", "transaction"]:
                order = self._orders.get(rid)
                if not order:
                    for o in self._orders.values():
                        if o.transaction_id == rid:
                            order = o
                            break
                if order:
                    record_data = order.model_dump()
            elif rtype == "customer":
                cust = self._customers.get(rid)
                if cust:
                    record_data = cust.model_dump()
            elif rtype == "lead":
                lead = self._leads.get(rid)
                if lead:
                    record_data = lead.model_dump()

            if not record_data:
                return {
                    "record_type": rtype,
                    "record_id": rid,
                    "exists": False,
                    "matches_expected": False,
                    "discrepancies": ["Record not found in system"],
                }

            discrepancies = []
            for field, expected_val in expected_fields.items():
                actual_val = record_data.get(field)
                if actual_val != expected_val:
                    discrepancies.append(
                        f"Field '{field}': expected '{expected_val}', found '{actual_val}'"
                    )

            return {
                "record_type": rtype,
                "record_id": rid,
                "exists": True,
                "matches_expected": len(discrepancies) == 0,
                "discrepancies": discrepancies,
            }

    async def create_activity(
        self,
        task_id: str,
        activity_type: str,
        description: str,
    ) -> ActivityRecord:
        activity_id = f"act_{uuid.uuid4().hex[:10]}"
        record = ActivityRecord(
            activity_id=activity_id,
            task_id=task_id,
            type=activity_type,
            description=description,
        )
        async with self._lock:
            self._activities[activity_id] = record
            return record.model_copy()

    async def get_activity(self, activity_id: str) -> Optional[ActivityRecord]:
        async with self._lock:
            act = self._activities.get(activity_id)
            return act.model_copy() if act else None

    async def get_activities_for_task(self, task_id: str) -> List[ActivityRecord]:
        async with self._lock:
            return [
                act.model_copy()
                for act in self._activities.values()
                if act.task_id == task_id
            ]


# Global singleton instance
_data_service_instance = DemoDataService()


def get_data_service() -> IDataService:
    """Return configured data service instance."""
    return _data_service_instance
