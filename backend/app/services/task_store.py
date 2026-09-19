import asyncio
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from app.models.task import Task, TaskStatus


class BaseTaskStore(ABC):
    """Abstract persistence interface for AgentX tasks.
    
    Prepares the architecture to swap between In-Memory store and Supabase PostgreSQL.
    """

    @abstractmethod
    async def save_task(self, task: Task) -> Task:
        """Persist a new task."""
        pass

    @abstractmethod
    async def get_task(self, task_id: str) -> Optional[Task]:
        """Fetch task by ID."""
        pass

    @abstractmethod
    async def update_task(self, task: Task) -> Task:
        """Update an existing task."""
        pass

    @abstractmethod
    async def list_tasks(self, limit: int = 50) -> List[Task]:
        """List tasks with limit."""
        pass


class InMemoryTaskStore(BaseTaskStore):
    """Thread-safe in-memory task repository for Phase 2."""

    def __init__(self):
        self._tasks: Dict[str, Task] = {}
        self._lock = asyncio.Lock()
        self._seed_demo_tasks()

    def _seed_demo_tasks(self) -> None:
        """Seed initial backward-compatible demo tasks."""
        demo_task = Task(
            task_id="TASK-9042",
            user_request="Customer Kaushal (k8849819@gmail.com) reported high dissatisfaction with order #ORD-8821. Package delivered late and 1 item missing.",
            selected_agent=None,
            agent_id="support",
            workspace_id="ws_default",
            created_by="usr_demo_owner",
            status=TaskStatus.WAITING_FOR_APPROVAL,
            approval_required=True,
            current_approval_id="APP-1029",
            result={
                "task_id": "TASK-9042",
                "customer": "CUST-001",
                "customer_name": "Kaushal",
                "customer_email": "k8849819@gmail.com",
                "order_id": "ORD-8821",
                "issue": "Shipping Delay & Missing Item",
                "summary": "Task awaiting manager sign-off to execute final email response to Kaushal (k8849819@gmail.com)."
            }
        )
        self._tasks[demo_task.task_id] = demo_task

    async def save_task(self, task: Task) -> Task:
        async with self._lock:
            self._tasks[task.task_id] = task.model_copy(deep=True)
            return task

    async def get_task(self, task_id: str) -> Optional[Task]:
        async with self._lock:
            task = self._tasks.get(task_id)
            return task.model_copy(deep=True) if task else None

    async def update_task(self, task: Task) -> Task:
        async with self._lock:
            self._tasks[task.task_id] = task.model_copy(deep=True)
            return task

    async def list_tasks(self, limit: int = 50) -> List[Task]:
        async with self._lock:
            tasks = list(self._tasks.values())
            # Return most recent tasks first
            tasks.sort(key=lambda t: t.created_at, reverse=True)
            return [t.model_copy(deep=True) for t in tasks[:limit]]

    # Convenience aliases
    async def create(self, task: Task) -> Task:
        return await self.save_task(task)

    async def get(self, task_id: str) -> Optional[Task]:
        return await self.get_task(task_id)

    async def update(self, task: Task) -> Task:
        return await self.update_task(task)


# Global singleton instance for in-memory persistence
_global_task_store = InMemoryTaskStore()


def get_task_store() -> BaseTaskStore:
    """Return configured task persistence store."""
    return _global_task_store
