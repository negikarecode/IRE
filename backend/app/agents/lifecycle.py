from typing import Dict, List, Callable, Optional, Set
import logging
from app.agents.registry import agent_registry, AgentStatus

logger = logging.getLogger("agent_lifecycle")

class InvalidStateTransitionException(ValueError):
    """Exception raised when an invalid agent lifecycle state transition is attempted."""
    pass

class AgentLifecycleManager:
    """
    Enterprise Agent Lifecycle State Machine Manager.
    Validates state transitions and triggers lifecycle event hooks.
    """
    # Valid lifecycle state transitions map
    VALID_TRANSITIONS: Dict[AgentStatus, Set[AgentStatus]] = {
        AgentStatus.INITIALIZED: {AgentStatus.IDLE, AgentStatus.PLANNING, AgentStatus.TERMINATED},
        AgentStatus.IDLE: {AgentStatus.PLANNING, AgentStatus.RUNNING, AgentStatus.PAUSED, AgentStatus.TERMINATED},
        AgentStatus.PLANNING: {AgentStatus.RUNNING, AgentStatus.FAILED, AgentStatus.PAUSED, AgentStatus.TERMINATED},
        AgentStatus.RUNNING: {AgentStatus.WAITING_FOR_INPUT, AgentStatus.COMPLETED, AgentStatus.PAUSED, AgentStatus.FAILED, AgentStatus.TERMINATED},
        AgentStatus.WAITING_FOR_INPUT: {AgentStatus.RUNNING, AgentStatus.PAUSED, AgentStatus.FAILED, AgentStatus.TERMINATED},
        AgentStatus.COMPLETED: {AgentStatus.IDLE, AgentStatus.PLANNING, AgentStatus.TERMINATED},
        AgentStatus.PAUSED: {AgentStatus.RUNNING, AgentStatus.IDLE, AgentStatus.TERMINATED},
        AgentStatus.FAILED: {AgentStatus.IDLE, AgentStatus.PLANNING, AgentStatus.TERMINATED},
        AgentStatus.TERMINATED: set()  # Terminal state
    }

    def __init__(self):
        self._listeners: List[Callable[[str, AgentStatus, AgentStatus], None]] = []

    def add_listener(self, listener: Callable[[str, AgentStatus, AgentStatus], None]) -> None:
        self._listeners.append(listener)

    def transition(self, agent_id: str, new_status: AgentStatus, task_id: Optional[str] = None) -> AgentStatus:
        agent = agent_registry.get_agent(agent_id)
        if not agent:
            raise ValueError(f"Agent '{agent_id}' not found in registry.")

        current_status = agent.status

        # If already in target status, return
        if current_status == new_status:
            return current_status

        # Validate transition
        allowed = self.VALID_TRANSITIONS.get(current_status, set())
        if new_status not in allowed:
            raise InvalidStateTransitionException(
                f"Invalid lifecycle transition for agent '{agent_id}': cannot transition from {current_status.value} to {new_status.value}."
            )

        # Update registry status
        agent_registry.update_status(agent_id, new_status, task_id)
        logger.info(f"Agent '{agent_id}' lifecycle transitioned: {current_status.value} -> {new_status.value}")

        # Notify listeners
        for listener in self._listeners:
            try:
                listener(agent_id, current_status, new_status)
            except Exception as e:
                logger.error(f"Error in lifecycle listener: {str(e)}")

        return new_status

    def pause_agent(self, agent_id: str) -> AgentStatus:
        return self.transition(agent_id, AgentStatus.PAUSED)

    def resume_agent(self, agent_id: str) -> AgentStatus:
        return self.transition(agent_id, AgentStatus.RUNNING)

    def terminate_agent(self, agent_id: str) -> AgentStatus:
        return self.transition(agent_id, AgentStatus.TERMINATED)

agent_lifecycle_manager = AgentLifecycleManager()
