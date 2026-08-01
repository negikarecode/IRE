from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
import time

@dataclass
class IntegrationMessage:
    message_id: str
    tenant_id: str
    connector_id: str
    protocol: str  # REST, SOAP, FHIR, WEBHOOK, POLLING
    payload: Any
    headers: Dict[str, str] = field(default_factory=dict)
    params: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

@dataclass
class IntegrationResponse:
    success: bool
    status_code: int
    data: Any
    error_message: Optional[str] = None
    latency_ms: float = 0.0

class BaseConnector(ABC):
    """
    Abstract Base Class for all Enterprise Integration Connectors (SDK).
    CRITICAL: EVERY integration connector MUST inherit from BaseConnector.
    Framework only — zero hospital or insurer business logic hardcoded.
    """
    def __init__(self, connector_id: str, name: str, endpoint_url: str):
        self.connector_id = connector_id
        self.name = name
        self.endpoint_url = endpoint_url
        self.is_connected = False

    @abstractmethod
    async def connect(self) -> bool:
        pass

    @abstractmethod
    async def authenticate(self) -> bool:
        pass

    @abstractmethod
    async def send(self, message: IntegrationMessage) -> IntegrationResponse:
        pass

    @abstractmethod
    async def receive(self) -> Optional[IntegrationMessage]:
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        pass
