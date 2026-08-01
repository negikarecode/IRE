from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class IClaimProcessor(ABC):
    """
    Interface for future claim adjudication and reasoning algorithms.
    Zero insurance or medical logic implemented in the platform architecture skeleton.
    """
    
    @abstractmethod
    async def process_claim(self, tenant_id: str, claim_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Subclasses or domain extensions will implement the reasoning pipeline.
        """
        pass

    @abstractmethod
    async def calculate_risk_score(self, tenant_id: str, payload: Dict[str, Any]) -> float:
        pass
