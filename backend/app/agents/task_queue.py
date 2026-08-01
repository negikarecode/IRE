from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
import uuid
import time

class TaskPriority:
    HIGH = 300
    MEDIUM = 200
    LOW = 100

@dataclass
class AgentTask:
    task_id: str
    tenant_id: str
    agent_id: str
    goal: str
    status: str  # QUEUED, IN_PROGRESS, COMPLETED, FAILED, CANCELLED
    priority: int = TaskPriority.MEDIUM
    session_id: str = "default_session"
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class AgentTaskQueue:
    """
    Priority Task Queue for Agent Background Execution Scheduling.
    Executes highest priority tasks first.
    """
    def __init__(self):
        self._tasks: Dict[str, AgentTask] = {}

    def submit_task(
        self,
        tenant_id: str,
        agent_id: str,
        goal: str,
        priority: int = TaskPriority.MEDIUM,
        session_id: str = "default_session"
    ) -> AgentTask:
        task_id = f"task_agent_{uuid.uuid4().hex[:8]}"
        task = AgentTask(
            task_id=task_id,
            tenant_id=tenant_id,
            agent_id=agent_id,
            goal=goal,
            status="QUEUED",
            priority=priority,
            session_id=session_id
        )
        self._tasks[task_id] = task
        return task

    def pop_next_task(self) -> Optional[AgentTask]:
        """
        Retrieves the next highest priority QUEUED task.
        """
        queued_tasks = [t for t in self._tasks.values() if t.status == "QUEUED"]
        if not queued_tasks:
            return None

        # Sort by priority desc, then created_at asc
        queued_tasks.sort(key=lambda t: (-t.priority, t.created_at))
        task = queued_tasks[0]
        task.status = "IN_PROGRESS"
        task.started_at = time.time()
        return task

    def get_task(self, task_id: str) -> Optional[AgentTask]:
        return self._tasks.get(task_id)

    def list_tasks_by_tenant(self, tenant_id: str) -> List[AgentTask]:
        tasks = [t for t in self._tasks.values() if t.tenant_id == tenant_id]
        tasks.sort(key=lambda t: t.created_at, reverse=True)
        return tasks

    def update_task_result(self, task_id: str, status: str, result: Optional[Dict[str, Any]] = None, error: Optional[str] = None) -> None:
        task = self.get_task(task_id)
        if task:
            task.status = status
            task.completed_at = time.time()
            task.result = result
            task.error = error

agent_task_queue = AgentTaskQueue()
