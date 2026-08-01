from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import time
from app.ai.vector_store import vector_store, VectorRecord
from app.ai.embedding_service import embedding_service

@dataclass
class ConversationTurn:
    turn_id: str
    role: str  # system, user, assistant, tool
    content: str
    tool_calls: Optional[List[Dict[str, Any]]] = None
    timestamp: float = field(default_factory=time.time)

class IConversationMemory(ABC):
    @abstractmethod
    def add_turn(self, role: str, content: str, tool_calls: Optional[List[Dict[str, Any]]] = None) -> ConversationTurn:
        pass

    @abstractmethod
    def get_history(self) -> List[ConversationTurn]:
        pass

    @abstractmethod
    def clear(self) -> None:
        pass

class SlidingWindowMemory(IConversationMemory):
    """
    Sliding Window Conversation Memory retaining the last max_window turns.
    """
    def __init__(self, session_id: str, tenant_id: str = "default", max_window: int = 10):
        self.session_id = session_id
        self.tenant_id = tenant_id
        self.max_window = max_window
        self.history: List[ConversationTurn] = []

    def add_turn(self, role: str, content: str, tool_calls: Optional[List[Dict[str, Any]]] = None) -> ConversationTurn:
        turn = ConversationTurn(
            turn_id=f"turn_{len(self.history) + 1}_{int(time.time() * 1000)}",
            role=role,
            content=content,
            tool_calls=tool_calls
        )
        self.history.append(turn)
        if len(self.history) > self.max_window:
            self.history = self.history[-self.max_window:]
        return turn

    def get_history(self) -> List[ConversationTurn]:
        return self.history

    def clear(self) -> None:
        self.history.clear()

class SummaryConversationMemory(IConversationMemory):
    """
    Summary Conversation Memory maintaining a concise running summary of past interactions
    plus a recent buffer of active turns.
    """
    def __init__(self, session_id: str, tenant_id: str = "default", buffer_size: int = 4):
        self.session_id = session_id
        self.tenant_id = tenant_id
        self.buffer_size = buffer_size
        self.summary: str = ""
        self.recent_turns: List[ConversationTurn] = []

    def add_turn(self, role: str, content: str, tool_calls: Optional[List[Dict[str, Any]]] = None) -> ConversationTurn:
        turn = ConversationTurn(
            turn_id=f"summary_turn_{int(time.time() * 1000)}",
            role=role,
            content=content,
            tool_calls=tool_calls
        )
        self.recent_turns.append(turn)
        if len(self.recent_turns) > self.buffer_size:
            overflow = self.recent_turns.pop(0)
            # Append overflow turn to running summary
            self.summary += f"\n[{overflow.role}]: {overflow.content}"
        return turn

    def get_history(self) -> List[ConversationTurn]:
        res = []
        if self.summary:
            res.append(ConversationTurn(
                turn_id="summary_context",
                role="system",
                content=f"Summary of prior conversation:\n{self.summary}"
            ))
        res.extend(self.recent_turns)
        return res

    def clear(self) -> None:
        self.summary = ""
        self.recent_turns.clear()

class VectorBackedLongTermMemory(IConversationMemory):
    """
    Long-Term Conversation Memory using Vector Store semantic indexing and recall.
    """
    def __init__(self, session_id: str, tenant_id: str = "default"):
        self.session_id = session_id
        self.tenant_id = tenant_id
        self.history: List[ConversationTurn] = []

    def add_turn(self, role: str, content: str, tool_calls: Optional[List[Dict[str, Any]]] = None) -> ConversationTurn:
        turn = ConversationTurn(
            turn_id=f"vec_turn_{len(self.history) + 1}_{int(time.time() * 1000)}",
            role=role,
            content=content,
            tool_calls=tool_calls
        )
        self.history.append(turn)
        return turn

    async def index_history(self) -> None:
        """
        Embed and store conversation turns in vector store for long-term semantic retrieval.
        """
        records = []
        for turn in self.history:
            vec = await embedding_service.embed_query(turn.content)
            records.append(VectorRecord(
                id=turn.turn_id,
                vector=vec,
                payload={"role": turn.role, "content": turn.content, "session_id": self.session_id},
                tenant_id=self.tenant_id,
                collection_name="conversation_memory"
            ))
        await vector_store.upsert(records, collection_name="conversation_memory")

    async def recall_relevant(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        query_vec = await embedding_service.embed_query(query)
        search_res = await vector_store.search(
            query_vector=query_vec,
            tenant_id=self.tenant_id,
            collection_name="conversation_memory",
            top_k=top_k
        )
        return [r.payload for r in search_res]

    def get_history(self) -> List[ConversationTurn]:
        return self.history

    def clear(self) -> None:
        self.history.clear()

class ConversationMemoryManager:
    """
    Central Multi-Tenant Manager for Session Conversation Memories.
    """
    def __init__(self):
        self._memories: Dict[str, IConversationMemory] = {}

    def get_or_create(self, session_id: str, tenant_id: str = "default", memory_type: str = "sliding") -> IConversationMemory:
        key = f"{tenant_id}:{session_id}"
        if key not in self._memories:
            if memory_type == "summary":
                self._memories[key] = SummaryConversationMemory(session_id, tenant_id)
            elif memory_type == "vector":
                self._memories[key] = VectorBackedLongTermMemory(session_id, tenant_id)
            else:
                self._memories[key] = SlidingWindowMemory(session_id, tenant_id)
        return self._memories[key]

    def clear_session(self, session_id: str, tenant_id: str = "default") -> bool:
        key = f"{tenant_id}:{session_id}"
        if key in self._memories:
            self._memories[key].clear()
            del self._memories[key]
            return True
        return False

conversation_memory_manager = ConversationMemoryManager()
