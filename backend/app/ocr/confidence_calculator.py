from typing import List, Dict, Any

class OCRConfidenceCalculator:
    """
    Computes page-level, section-level, and document-level confidence metrics.
    """
    def calculate_overall_confidence(
        self,
        text_confidence: float,
        layout_confidence: float,
        table_confidence: float
    ) -> Dict[str, float]:
        overall = (text_confidence * 0.5) + (layout_confidence * 0.3) + (table_confidence * 0.2)
        return {
            "overall_confidence": round(overall, 4),
            "text_confidence": round(text_confidence, 4),
            "layout_confidence": round(layout_confidence, 4),
            "table_confidence": round(table_confidence, 4)
        }

confidence_calculator = OCRConfidenceCalculator()
