import asyncio
from typing import Dict, List, Optional
from app.models.input import BusinessInput


class InputStore:
    """Thread-safe in-memory store for AgentX business inputs."""

    def __init__(self):
        self._inputs: Dict[str, BusinessInput] = {}
        self._task_index: Dict[str, List[str]] = {}
        self._lock = asyncio.Lock()

    async def save_input(self, business_input: BusinessInput) -> BusinessInput:
        """Store or update a business input."""
        async with self._lock:
            self._inputs[business_input.input_id] = business_input
            if business_input.task_id:
                if business_input.task_id not in self._task_index:
                    self._task_index[business_input.task_id] = []
                if business_input.input_id not in self._task_index[business_input.task_id]:
                    self._task_index[business_input.task_id].append(business_input.input_id)
        return business_input

    async def get_input(self, input_id: str) -> Optional[BusinessInput]:
        """Retrieve a business input by ID."""
        async with self._lock:
            return self._inputs.get(input_id)

    async def list_inputs_by_task(self, task_id: str) -> List[BusinessInput]:
        """List all inputs attached to a specific task."""
        async with self._lock:
            input_ids = self._task_index.get(task_id, [])
            return [self._inputs[iid] for iid in input_ids if iid in self._inputs]

    async def associate_task(self, input_id: str, task_id: str) -> bool:
        """Associate an existing input with a task ID."""
        async with self._lock:
            business_input = self._inputs.get(input_id)
            if not business_input:
                return False
            business_input.task_id = task_id
            if task_id not in self._task_index:
                self._task_index[task_id] = []
            if input_id not in self._task_index[task_id]:
                self._task_index[task_id].append(input_id)
            return True

    async def delete_input(self, input_id: str) -> bool:
        """Remove an input from the store."""
        async with self._lock:
            if input_id in self._inputs:
                inp = self._inputs.pop(input_id)
                if inp.task_id and inp.task_id in self._task_index:
                    if input_id in self._task_index[inp.task_id]:
                        self._task_index[inp.task_id].remove(input_id)
                return True
            return False

    async def clear(self) -> None:
        """Clear all inputs (for test isolation)."""
        async with self._lock:
            self._inputs.clear()
            self._task_index.clear()


_input_store: Optional[InputStore] = None


def get_input_store() -> InputStore:
    """Return singleton instance of InputStore."""
    global _input_store
    if _input_store is None:
        _input_store = InputStore()
    return _input_store
