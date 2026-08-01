from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
import time
from app.ai.guardrails import domain_guardrail, DomainPolicyViolationException

class AgentStatus(str, Enum):
    INITIALIZED = "INITIALIZED"
    IDLE = "IDLE"
    PLANNING = "PLANNING"
    RUNNING = "RUNNING"
    WAITING_FOR_INPUT = "WAITING_FOR_INPUT"
    COMPLETED = "COMPLETED"
    PAUSED = "PAUSED"
    FAILED = "FAILED"
    TERMINATED = "TERMINATED"

@dataclass
class AgentMetadata:
    """
    Provider-Agnostic Agent Specification Metadata.
    Zero domain logic hardcoded.
    """
    agent_id: str
    name: str
    role_description: str
    system_prompt: str
    primary_model: str = "gpt-4o"
    allowed_tools: List[str] = field(default_factory=list)
    status: AgentStatus = AgentStatus.INITIALIZED
    current_task_id: Optional[str] = None
    created_at: float = field(default_factory=time.time)

class AgentRegistry:
    """
    Central Agent Registry managing autonomous agent definitions, roles, capabilities, and live state.
    Includes Domain Policy Guardrails ensuring zero medical/insurance agents are registered.
    """
    def __init__(self):
        self._agents: Dict[str, AgentMetadata] = {}
        self._seed_default_agents()

    def _seed_default_agents(self):
        # Register standard generic agent
        self.register_agent(AgentMetadata(
            agent_id="general_assistant_agent",
            name="General Technical Assistant Agent",
            role_description="Generic autonomous agent for software design and data analysis",
            system_prompt="You are an autonomous AI software architecture assistant.",
            primary_model="gpt-4o",
            allowed_tools=["http_request", "data_transform", "math_solver"]
        ))

    def register_agent(self, metadata: AgentMetadata) -> None:
        """
        Registers an agent after validating domain policy guardrails (No medical / insurance prompts allowed).
        """
        domain_guardrail.enforce_policy(metadata.system_prompt, context_name=f"Agent '{metadata.agent_id}' System Prompt")
        domain_guardrail.enforce_policy(metadata.role_description, context_name=f"Agent '{metadata.agent_id}' Role Description")

        self._agents[metadata.agent_id] = metadata

    def get_agent(self, agent_id: str) -> Optional[AgentMetadata]:
        return self._agents.get(agent_id)

    def list_agents(self) -> List[AgentMetadata]:
        return list(self._agents.values())

    def unregister_agent(self, agent_id: str) -> bool:
        if agent_id in self._agents:
            del self._agents[agent_id]
            return True
        return False

    def update_status(self, agent_id: str, status: AgentStatus, task_id: Optional[str] = None) -> None:
        agent = self.get_agent(agent_id)
        if agent:
            agent.status = status
            if task_id is not None:
                agent.current_task_id = task_id

agent_registry = AgentRegistry()
