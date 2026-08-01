from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import time

@dataclass
class ConversationTurn:
    turn_id: str
    role: str  # system, user, assistant, tool
    content: str
    tool_calls: Optional[List[Dict[str, Any]]] = None
    timestamp: float = field(default_factory=time.time)

class ConversationMemory:
    """
    Session/Thread Conversation Memory for single agent interactions.
    """
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.history: List[ConversationTurn] = []

    def add_turn(self, role: str, content: str, tool_calls: Optional[List[Dict[str, Any]]] = None) -> None:
        turn = ConversationTurn(
            turn_id=f"turn_{len(self.history) + 1}_{int(time.time())}",
            role=role,
            content=content,
            tool_calls=tool_calls
        )
        self.history.append(turn)

    def get_history(self) -> List[ConversationTurn]:
        return self.history

class SharedAgentMemory:
    """
    Cross-Agent Shared Key-Value & Context Memory for multi-agent collaboration.
    Isolation scoped by tenant_id.
    """
    def __init__(self):
        self._shared_store: Dict[str, Dict[str, Any]] = {}

    def set_context(self, tenant_id: str, key: str, value: Any) -> None:
        if tenant_id not in self._shared_store:
            self._shared_store[tenant_id] = {}
        self._shared_store[tenant_id][key] = value

    def get_context(self, tenant_id: str, key: str) -> Optional[Any]:
        return self._shared_store.get(tenant_id, {}).get(key)

    def list_keys(self, tenant_id: str) -> List[str]:
        return list(self._shared_store.get(tenant_id, {}).keys())

shared_agent_memory = SharedAgentMemory()
