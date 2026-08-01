from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable
import time
import uuid

@dataclass
class AgentMessage:
    message_id: str
    sender_agent_id: str
    recipient_agent_id: Optional[str]  # None if topic broadcast
    message_type: str                  # REQUEST, RESPONSE, DELEGATION, BROADCAST
    content: Dict[str, Any]
    topic: Optional[str] = None
    timestamp: float = field(default_factory=time.time)

class AgentCommunicationBus:
    """
    Inter-Agent Communication Bus supporting Point-to-Point Direct Messaging
    and Event-Driven Publish/Subscribe Topic Channels.
    """
    def __init__(self):
        # {agent_id: List[AgentMessage]}
        self._inboxes: Dict[str, List[AgentMessage]] = {}
        # {topic: List[AgentMessage]}
        self._topics: Dict[str, List[AgentMessage]] = {}
        # {topic: List[Callable[[AgentMessage], None]]}
        self._subscriptions: Dict[str, List[Callable[[AgentMessage], None]]] = {}

    def send_message(self, message: AgentMessage) -> None:
        if message.recipient_agent_id:
            if message.recipient_agent_id not in self._inboxes:
                self._inboxes[message.recipient_agent_id] = []
            self._inboxes[message.recipient_agent_id].append(message)

    def receive_messages(self, recipient_agent_id: str) -> List[AgentMessage]:
        messages = self._inboxes.get(recipient_agent_id, [])
        self._inboxes[recipient_agent_id] = []
        return messages

    def publish(self, topic: str, sender_id: str, content: Dict[str, Any]) -> AgentMessage:
        msg = AgentMessage(
            message_id=f"msg_{uuid.uuid4().hex[:8]}",
            sender_agent_id=sender_id,
            recipient_agent_id=None,
            message_type="BROADCAST",
            content=content,
            topic=topic
        )
        if topic not in self._topics:
            self._topics[topic] = []
        self._topics[topic].append(msg)

        # Notify active subscribers
        for handler in self._subscriptions.get(topic, []):
            try:
                handler(msg)
            except Exception:
                pass

        return msg

    def subscribe(self, topic: str, handler: Callable[[AgentMessage], None]) -> None:
        if topic not in self._subscriptions:
            self._subscriptions[topic] = []
        self._subscriptions[topic].append(handler)

    def get_topic_messages(self, topic: str) -> List[AgentMessage]:
        return self._topics.get(topic, [])

agent_comm_bus = AgentCommunicationBus()
