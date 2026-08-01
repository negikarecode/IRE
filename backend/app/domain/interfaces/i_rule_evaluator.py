from abc import ABC, abstractmethod
from typing import Dict, Any, List

class IRuleEvaluator(ABC):
    """
    Interface for pluggable rule evaluation AST/WASM engine.
    """
    
    @abstractmethod
    async def evaluate_rules(self, tenant_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        pass
