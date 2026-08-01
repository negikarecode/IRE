import hashlib
import json
import time
from typing import Optional, Dict, Any, List
from app.ai.embedding_service import embedding_service
from app.ai.vector_store import vector_store, VectorRecord

class AICacheManager:
    """
    Multi-Tier Provider-Independent AI Cache Manager featuring:
    1. Exact Hash Matching (SHA-256).
    2. Semantic Caching via Vector Similarity Search.
    3. Cache Telemetry & Hit Ratio tracking.
    4. TTL Expiration & Tenant Isolation.
    """
    def __init__(self, default_ttl: int = 3600, semantic_similarity_threshold: float = 0.92):
        self.default_ttl = default_ttl
        self.semantic_similarity_threshold = semantic_similarity_threshold
        # {hash_key: {"response": str, "timestamp": float, "ttl": int}}
        self._exact_cache: Dict[str, Dict[str, Any]] = {}
        # Telemetry counters
        self.hits = 0
        self.misses = 0

    def _compute_key(self, tenant_id: str, prompt: str, model_id: str) -> str:
        raw_key = f"{tenant_id}:{model_id}:{prompt.strip()}"
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

    async def get_exact(self, tenant_id: str, prompt: str, model_id: str) -> Optional[str]:
        cache_key = self._compute_key(tenant_id, prompt, model_id)
        entry = self._exact_cache.get(cache_key)
        if not entry:
            return None

        # Check TTL
        if time.time() - entry["timestamp"] > entry["ttl"]:
            del self._exact_cache[cache_key]
            return None

        self.hits += 1
        return entry["response"]

    async def set_exact(self, tenant_id: str, prompt: str, model_id: str, response: str, ttl: Optional[int] = None) -> None:
        cache_key = self._compute_key(tenant_id, prompt, model_id)
        self._exact_cache[cache_key] = {
            "response": response,
            "timestamp": time.time(),
            "ttl": ttl or self.default_ttl
        }

    async def get_semantic(self, tenant_id: str, prompt: str, model_id: str) -> Optional[str]:
        """
        Performs semantic vector lookup for prompt against previously cached prompts.
        """
        # First attempt exact match
        exact_res = await self.get_exact(tenant_id, prompt, model_id)
        if exact_res:
            return exact_res

        # Calculate query prompt vector
        query_vec = await embedding_service.embed_query(prompt)
        search_results = await vector_store.search(
            query_vector=query_vec,
            tenant_id=tenant_id,
            collection_name="semantic_cache",
            top_k=1
        )

        if search_results and search_results[0].score >= self.semantic_similarity_threshold:
            self.hits += 1
            return search_results[0].payload.get("response")

        self.misses += 1
        return None

    async def set_semantic(self, tenant_id: str, prompt: str, model_id: str, response: str) -> None:
        # Also store exact match
        await self.set_exact(tenant_id, prompt, model_id, response)

        # Store in vector store for semantic retrieval
        prompt_vec = await embedding_service.embed_query(prompt)
        record_id = f"cache_{hashlib.md5(f'{tenant_id}:{prompt}'.encode('utf-8')).hexdigest()}"
        
        record = VectorRecord(
            id=record_id,
            vector=prompt_vec,
            payload={
                "prompt": prompt,
                "model_id": model_id,
                "response": response,
                "cached_at": time.time()
            },
            tenant_id=tenant_id,
            collection_name="semantic_cache"
        )
        await vector_store.upsert([record], collection_name="semantic_cache")

    def get_stats(self) -> Dict[str, Any]:
        total = self.hits + self.misses
        ratio = (self.hits / total) if total > 0 else 0.0
        return {
            "hits": self.hits,
            "misses": self.misses,
            "total_requests": total,
            "hit_ratio": round(ratio, 4),
            "exact_cache_size": len(self._exact_cache)
        }

    def clear(self) -> None:
        self._exact_cache.clear()
        self.hits = 0
        self.misses = 0

ai_cache = AICacheManager()
