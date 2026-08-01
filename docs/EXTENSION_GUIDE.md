# Extension Guide: Extending Connectors, Storage & LLM Adapters

This guide explains how engineers can extend the **Insurance Reasoning Engine (IRE)** infrastructure by implementing abstract base contracts for custom connectors, vector databases, and LLM providers.

---

## 1. Adding a New Integration Connector (`BaseConnector`)

Every integration connector in the platform **MUST** inherit from `BaseConnector` ([`backend/app/integration/base_connector.py`](file:///home/aryan/Videos/IRE/backend/app/integration/base_connector.py)).

### Step-by-Step Connector Implementation

```python
from app.integration.base_connector import BaseConnector, IntegrationMessage, IntegrationResponse
from app.integration.registry import connector_registry

class CustomEnterpriseConnector(BaseConnector):
    """
    Custom Connector inheriting from BaseConnector.
    """
    async def connect(self) -> bool:
        self.is_connected = True
        return True

    async def authenticate(self) -> bool:
        # Custom authentication logic (OAuth2, Mutual TLS, API Key)
        return True

    async def send(self, message: IntegrationMessage) -> IntegrationResponse:
        # Custom protocol transport logic
        return IntegrationResponse(
            success=True,
            status_code=200,
            data={"status": "DELIVERED", "target": self.endpoint_url}
        )

    async def receive(self) -> Optional[IntegrationMessage]:
        return None

    async def health_check(self) -> bool:
        return self.is_connected

    async def disconnect(self) -> None:
        self.is_connected = False

# Register connector instance
connector_registry.register(
    CustomEnterpriseConnector("conn_custom_01", "Custom System Endpoint", "https://api.custom.org")
)
```

---

## 2. Adding a New Vector Database Adapter (`IVectorStore`)

To integrate a new vector database (e.g. Qdrant, PGVector, Milvus, Pinecone), implement `IVectorStore` ([`backend/app/ai/vector_store.py`](file:///home/aryan/Videos/IRE/backend/app/ai/vector_store.py)):

```python
from app.ai.vector_store import IVectorStore, VectorRecord
from typing import List

class QdrantVectorStoreAdapter(IVectorStore):
    async def upsert(self, tenant_id: str, records: List[VectorRecord]) -> None:
        # Qdrant client upsert implementation with tenant metadata filter
        pass

    async def search(self, tenant_id: str, query_vector: List[float], top_k: int = 5) -> List[VectorRecord]:
        # Qdrant client search implementation
        return []
```

---

## 3. Adding a New LLM Provider (`ILLMProviderAdapter`)

To add support for a new LLM provider (e.g. Cohere, DeepSeek, AWS Bedrock), implement `ILLMProviderAdapter` ([`backend/app/ai/llm_gateway.py`](file:///home/aryan/Videos/IRE/backend/app/ai/llm_gateway.py)):

```python
from app.ai.llm_gateway import ILLMProviderAdapter, LLMRequest, LLMResponse

class CustomLLMProviderAdapter(ILLMProviderAdapter):
    async def generate(self, request: LLMRequest, model_id: str) -> LLMResponse:
        # API Client call to provider
        return LLMResponse(
            content="Generated text output",
            model_used=model_id,
            provider_used="custom_provider",
            input_tokens=100,
            output_tokens=50,
            latency_ms=120.0
        )
```

By adhering to object-oriented inheritance and interface segregation, the core infrastructure remains stable while supporting unlimited external integration targets.
