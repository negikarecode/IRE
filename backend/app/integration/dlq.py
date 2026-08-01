from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import time
from app.integration.base_connector import IntegrationMessage, IntegrationResponse
from app.integration.registry import connector_registry

@dataclass
class DLQRecord:
    dlq_id: str
    tenant_id: str
    connector_id: str
    message: IntegrationMessage
    error_reason: str
    retry_count: int
    failed_at: float = field(default_factory=time.time)

class DeadLetterQueueManager:
    """
    Dead Letter Queue (DLQ) Manager for recording failed integration messages after retry exhaustion.
    Provides message inspection, purging, and retry replay.
    """
    def __init__(self):
        self._dlq_store: Dict[str, DLQRecord] = {}

    def push(
        self,
        tenant_id: str,
        connector_id: str,
        message: IntegrationMessage,
        error_reason: str,
        retry_count: int
    ) -> str:
        dlq_id = f"dlq_{len(self._dlq_store) + 1}_{int(time.time() * 1000)}"
        record = DLQRecord(
            dlq_id=dlq_id,
            tenant_id=tenant_id,
            connector_id=connector_id,
            message=message,
            error_reason=error_reason,
            retry_count=retry_count
        )
        self._dlq_store[dlq_id] = record
        return dlq_id

    def list_by_tenant(self, tenant_id: str) -> List[DLQRecord]:
        return [r for r in self._dlq_store.values() if r.tenant_id == tenant_id]

    def get(self, dlq_id: str) -> Optional[DLQRecord]:
        return self._dlq_store.get(dlq_id)

    def remove(self, dlq_id: str) -> bool:
        if dlq_id in self._dlq_store:
            del self._dlq_store[dlq_id]
            return True
        return False

    async def replay(self, dlq_id: str) -> IntegrationResponse:
        record = self.get(dlq_id)
        if not record:
            raise ValueError(f"DLQ Record '{dlq_id}' not found.")

        connector = connector_registry.get(record.connector_id)
        if not connector:
            raise ValueError(f"Connector '{record.connector_id}' not found in registry.")

        # Attempt re-sending message
        response = await connector.send(record.message)
        if response.success:
            self.remove(dlq_id)

        return response

dlq_manager = DeadLetterQueueManager()
