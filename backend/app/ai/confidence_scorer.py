from dataclasses import dataclass
from typing import Dict, Any, List

@dataclass
class ConfidenceReport:
    score: float  # 0.0 to 1.0
    requires_hitl: bool
    confidence_level: str  # HIGH, MEDIUM, LOW
    breakdown: Dict[str, float]

class ConfidenceScoringFramework:
    """
    Confidence Scoring Engine for LLM outputs and automated decisions.
    Determines Human-In-The-Loop (HITL) escalation requirements.
    """
    def __init__(self, hitl_threshold: float = 0.85):
        self.hitl_threshold = hitl_threshold

    def calculate_score(
        self,
        logprob_score: float = 0.95,
        consistency_score: float = 0.90,
        retrieval_relevance_score: float = 0.88
    ) -> ConfidenceReport:
        # Weighted confidence calculation
        weights = {"logprob": 0.4, "consistency": 0.3, "retrieval": 0.3}
        final_score = (
            (logprob_score * weights["logprob"]) +
            (consistency_score * weights["consistency"]) +
            (retrieval_relevance_score * weights["retrieval"])
        )

        requires_hitl = final_score < self.hitl_threshold

        if final_score >= 0.90:
            level = "HIGH"
        elif final_score >= 0.75:
            level = "MEDIUM"
        else:
            level = "LOW"

        return ConfidenceReport(
            score=round(final_score, 4),
            requires_hitl=requires_hitl,
            confidence_level=level,
            breakdown={
                "logprob": logprob_score,
                "consistency": consistency_score,
                "retrieval": retrieval_relevance_score
            }
        )

confidence_scorer = ConfidenceScoringFramework()
