import hashlib
from typing import Dict, Any, Optional
from app.rules.sandbox import safe_sandbox

class RuleCacheManager:
    """
    In-Memory & Redis Rule AST Compilation & Query Cache.
    Drastically accelerates execution throughput by caching compiled AST code objects.
    """
    def __init__(self):
        # {condition_hash: compiled_code_obj}
        self._compiled_cache: Dict[str, Any] = {}
        self.hits = 0
        self.misses = 0

    def _hash_condition(self, condition: str) -> str:
        return hashlib.sha256(condition.strip().encode("utf-8")).hexdigest()

    def get_compiled(self, condition: str) -> Optional[Any]:
        c_hash = self._hash_condition(condition)
        code = self._compiled_cache.get(c_hash)
        if code:
            self.hits += 1
            return code
        self.misses += 1
        return None

    def set_compiled(self, condition: str, compiled_code: Any) -> None:
        c_hash = self._hash_condition(condition)
        self._compiled_cache[c_hash] = compiled_code

    def get_or_compile(self, condition: str) -> Any:
        cached = self.get_compiled(condition)
        if cached is not None:
            return cached

        tree = safe_sandbox.validate_ast(condition)
        compiled = compile(tree, filename="<rule_compiled_cache>", mode="eval")
        self.set_compiled(condition, compiled)
        return compiled

    def get_stats(self) -> Dict[str, Any]:
        total = self.hits + self.misses
        ratio = (self.hits / total) if total > 0 else 0.0
        return {
            "hits": self.hits,
            "misses": self.misses,
            "hit_ratio": round(ratio, 4),
            "cached_rules_count": len(self._compiled_cache)
        }

    def clear(self) -> None:
        self._compiled_cache.clear()
        self.hits = 0
        self.misses = 0

rule_cache = RuleCacheManager()
