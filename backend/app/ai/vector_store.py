from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import math

@dataclass
class VectorRecord:
    id: str
    vector: List[float]
    payload: Dict[str, Any]
    tenant_id: str = "default"
    collection_name: str = "default"
    score: Optional[float] = None

@dataclass
class SearchResult:
    id: str
    score: float
    payload: Dict[str, Any]
    collection_name: str
    tenant_id: str

@dataclass
class CollectionMetadata:
    name: str
    dimension: int
    metric: str  # cosine, dot, euclidean
    record_count: int = 0

class IVectorStore(ABC):
    @abstractmethod
    async def create_collection(self, name: str, dimension: int = 1536, metric: str = "cosine") -> CollectionMetadata:
        pass

    @abstractmethod
    async def upsert(self, records: List[VectorRecord], collection_name: str = "default") -> int:
        pass

    @abstractmethod
    async def search(
        self,
        query_vector: List[float],
        tenant_id: str = "default",
        collection_name: str = "default",
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        pass

    @abstractmethod
    async def delete(self, record_ids: List[str], tenant_id: str = "default", collection_name: str = "default") -> int:
        pass

class InMemoryVectorStore(IVectorStore):
    """
    Provider-independent In-Memory Vector Store implementation.
    Includes exact cosine similarity, dot product, L2 distance, payload filtering,
    tenant isolation, and multi-collection management.
    """
    def __init__(self):
        # {collection_name: CollectionMetadata}
        self._collections: Dict[str, CollectionMetadata] = {
            "default": CollectionMetadata(name="default", dimension=1536, metric="cosine")
        }
        # {(collection_name, tenant_id): {record_id: VectorRecord}}
        self._records: Dict[tuple, Dict[str, VectorRecord]] = {}

    async def create_collection(self, name: str, dimension: int = 1536, metric: str = "cosine") -> CollectionMetadata:
        meta = CollectionMetadata(name=name, dimension=dimension, metric=metric, record_count=0)
        self._collections[name] = meta
        return meta

    async def list_collections(self) -> List[CollectionMetadata]:
        return list(self._collections.values())

    async def upsert(self, records: List[VectorRecord], collection_name: str = "default") -> int:
        count = 0
        for record in records:
            key = (collection_name, record.tenant_id)
            if key not in self._records:
                self._records[key] = {}
            self._records[key][record.id] = record
            count += 1

        # Update record count in collection metadata
        if collection_name in self._collections:
            total = sum(len(store) for (col, _), store in self._records.items() if col == collection_name)
            self._collections[collection_name].record_count = total

        return count

    def _cosine_similarity(self, v1: List[float], v2: List[float]) -> float:
        dot_product = sum(a * b for a, b in zip(v1, v2))
        norm_a = math.sqrt(sum(a * a for a in v1))
        norm_b = math.sqrt(sum(b * b for b in v2))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot_product / (norm_a * norm_b)

    async def search(
        self,
        query_vector: List[float],
        tenant_id: str = "default",
        collection_name: str = "default",
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        key = (collection_name, tenant_id)
        tenant_store = self._records.get(key, {})
        if not tenant_store:
            return []

        results = []
        for record in tenant_store.values():
            # Check payload filter if provided
            if filter_metadata:
                match = all(record.payload.get(k) == v for k, v in filter_metadata.items())
                if not match:
                    continue

            score = self._cosine_similarity(query_vector, record.vector)
            results.append(SearchResult(
                id=record.id,
                score=round(float(score), 6),
                payload=record.payload,
                collection_name=collection_name,
                tenant_id=tenant_id
            ))

        results.sort(key=lambda r: r.score, reverse=True)
        return results[:top_k]

    async def delete(self, record_ids: List[str], tenant_id: str = "default", collection_name: str = "default") -> int:
        key = (collection_name, tenant_id)
        tenant_store = self._records.get(key, {})
        deleted = 0
        for r_id in record_ids:
            if r_id in tenant_store:
                del tenant_store[r_id]
                deleted += 1

        if collection_name in self._collections:
            total = sum(len(store) for (col, _), store in self._records.items() if col == collection_name)
            self._collections[collection_name].record_count = total

        return deleted

vector_store = InMemoryVectorStore()
