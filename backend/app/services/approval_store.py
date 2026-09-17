import asyncio
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Union
from app.models.approval import ApprovalRecord, ApprovalStatus


class BaseApprovalStore(ABC):
    """Abstract persistence interface for approval records."""

    @abstractmethod
    async def save_approval(self, approval: ApprovalRecord) -> ApprovalRecord:
        pass

    @abstractmethod
    async def get_approval(self, approval_id: str) -> Optional[ApprovalRecord]:
        pass

    @abstractmethod
    async def get_approval_by_task_and_step(
        self,
        task_id: str,
        step_id: Union[int, str],
    ) -> Optional[ApprovalRecord]:
        pass

    @abstractmethod
    async def list_approvals(
        self,
        status: Optional[ApprovalStatus] = None,
        task_id: Optional[str] = None,
    ) -> List[ApprovalRecord]:
        pass

    @abstractmethod
    async def update_approval(self, approval: ApprovalRecord) -> ApprovalRecord:
        pass


class InMemoryApprovalStore(BaseApprovalStore):
    """Thread-safe in-memory store for human approval records."""

    def __init__(self):
        self._approvals: Dict[str, ApprovalRecord] = {}
        self._lock = asyncio.Lock()

    async def save_approval(self, approval: ApprovalRecord) -> ApprovalRecord:
        async with self._lock:
            self._approvals[approval.approval_id] = approval.model_copy(deep=True)
            return approval

    async def get_approval(self, approval_id: str) -> Optional[ApprovalRecord]:
        async with self._lock:
            appr = self._approvals.get(approval_id)
            return appr.model_copy(deep=True) if appr else None

    async def get_approval_by_task_and_step(
        self,
        task_id: str,
        step_id: Union[int, str],
    ) -> Optional[ApprovalRecord]:
        async with self._lock:
            for appr in self._approvals.values():
                if appr.task_id == task_id and str(appr.step_id) == str(step_id):
                    return appr.model_copy(deep=True)
            return None

    async def list_approvals(
        self,
        status: Optional[ApprovalStatus] = None,
        task_id: Optional[str] = None,
    ) -> List[ApprovalRecord]:
        async with self._lock:
            records = list(self._approvals.values())
            if status:
                records = [r for r in records if r.status == status]
            if task_id:
                records = [r for r in records if r.task_id == task_id]
            # Order newest first
            records.sort(key=lambda r: r.created_at, reverse=True)
            return [r.model_copy(deep=True) for r in records]

    async def update_approval(self, approval: ApprovalRecord) -> ApprovalRecord:
        async with self._lock:
            self._approvals[approval.approval_id] = approval.model_copy(deep=True)
            return approval

    # Convenience aliases
    async def save(self, approval: ApprovalRecord) -> ApprovalRecord:
        return await self.save_approval(approval)

    async def get(self, approval_id: str) -> Optional[ApprovalRecord]:
        return await self.get_approval(approval_id)

    async def update(self, approval: ApprovalRecord) -> ApprovalRecord:
        return await self.update_approval(approval)

    async def list(
        self,
        status: Optional[ApprovalStatus] = None,
        task_id: Optional[str] = None,
    ) -> List[ApprovalRecord]:
        return await self.list_approvals(status=status, task_id=task_id)



_global_approval_store = InMemoryApprovalStore()


def get_approval_store() -> BaseApprovalStore:
    """Return configured approval store instance."""
    return _global_approval_store
