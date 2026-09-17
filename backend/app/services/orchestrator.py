import logging
import uuid
from typing import Optional
from app.agents.router import AgentRouter
from app.models.task import AgentType, Task, TaskStatus
from app.services.execution_engine import TaskExecutionEngine, get_execution_engine
from app.services.task_store import BaseTaskStore, get_task_store
from app.services.verifier import TaskVerifier

logger = logging.getLogger(__name__)


class TaskOrchestrator:
    """Core orchestration engine coordinating AI teammates from request to completion.
    
    Pipeline:
    Understand → Select Agent → Plan → Execute → Verify → Complete
    """

    def __init__(
        self,
        task_store: Optional[BaseTaskStore] = None,
        router: Optional[AgentRouter] = None,
        execution_engine: Optional[TaskExecutionEngine] = None,
    ):
        self.store = task_store or get_task_store()
        self.router = router or AgentRouter()
        self.execution_engine = execution_engine or get_execution_engine()

    async def create_and_run_task(
        self,
        user_request: str,
        explicit_agent: Optional[str] = None,
    ) -> Task:
        """Initialize task record and immediately run the orchestration lifecycle."""
        task_id = f"task_{uuid.uuid4().hex[:12]}"
        
        # 1. Initialize Task
        task = Task(
            task_id=task_id,
            user_request=user_request,
            status=TaskStatus.CREATED,
        )
        task.add_event(
            stage=TaskStatus.CREATED,
            action="Initialized business task",
            summary=f"Received request: {user_request[:80]}...",
        )
        await self.store.save_task(task)

        # Run through lifecycle
        return await self.execute_task_lifecycle(task, explicit_agent)

    async def execute_task_lifecycle(
        self,
        task: Task,
        explicit_agent: Optional[str] = None,
    ) -> Task:
        """Execute the 5-stage orchestration lifecycle."""
        try:
            # Stage 1: Understand & Select Agent
            task.add_event(
                stage=TaskStatus.PLANNING,
                action="Routing request to appropriate teammate",
            )
            agent_type, agent = await self.router.route(task.user_request, explicit_agent)
            task.selected_agent = agent_type
            task.add_event(
                stage=TaskStatus.PLANNING,
                action=f"Assigned task to {agent.name} ({agent.role})",
                summary=f"Teammate identity established: {agent.name}",
            )

            # Stage 2: Task Planning
            plan = await agent.plan(task.user_request, task_id=task.task_id)
            plan_summary = getattr(plan, "plan_summary", None) or plan.objective
            task.plan = plan
            task.add_event(
                stage=TaskStatus.PLANNING,
                action="Formulated task execution plan",
                summary=plan_summary,
            )

            # Stages 3, 4, 5: Controlled Multi-Step Execution, Verification & Completion
            task = await self.execution_engine.execute_task(task, agent, plan)

        except Exception as exc:
            logger.exception("Orchestration encountered fatal error for task %s", task.task_id)
            task.status = TaskStatus.FAILED
            task.error = str(exc)
            task.add_event(
                stage=TaskStatus.FAILED,
                action="Encountered unhandled orchestration exception",
                status="FAILED",
                summary=str(exc),
            )

        # Update persistence store
        await self.store.update_task(task)
        return task


_global_orchestrator: Optional[TaskOrchestrator] = None


def get_orchestrator() -> TaskOrchestrator:
    """Return orchestrator instance."""
    global _global_orchestrator
    if _global_orchestrator is None:
        _global_orchestrator = TaskOrchestrator()
    return _global_orchestrator
