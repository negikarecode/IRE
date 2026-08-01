from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class OCRTelemetrySummary:
    total_processed_documents: int = 0
    total_pages_processed: int = 0
    average_latency_ms: float = 0.0
    average_confidence_score: float = 0.0
    total_table_grids_extracted: int = 0
    handwriting_recognition_count: int = 0
    error_count: int = 0

class OCRMonitoring:
    """
    Monitoring Telemetry for OCR Infrastructure.
    """
    def __init__(self):
        self._summary = OCRTelemetrySummary()

    def record_job_completion(
        self, 
        pages: int, 
        latency_ms: float, 
        confidence: float, 
        tables: int, 
        has_handwriting: bool,
        success: bool = True
    ) -> None:
        self._summary.total_processed_documents += 1
        if not success:
            self._summary.error_count += 1
            return

        self._summary.total_pages_processed += pages
        self._summary.total_table_grids_extracted += tables
        if has_handwriting:
            self._summary.handwriting_recognition_count += 1

        # Exponential moving average updates
        self._summary.average_latency_ms = (self._summary.average_latency_ms * 0.8) + (latency_ms * 0.2)
        self._summary.average_confidence_score = (self._summary.average_confidence_score * 0.8) + (confidence * 0.2)

    def get_metrics(self) -> Dict[str, Any]:
        return {
            "total_documents": self._summary.total_processed_documents,
            "total_pages": self._summary.total_pages_processed,
            "avg_latency_ms": round(self._summary.average_latency_ms, 2),
            "avg_confidence_score": round(self._summary.average_confidence_score, 4),
            "tables_extracted": self._summary.total_table_grids_extracted,
            "handwriting_jobs": self._summary.handwriting_recognition_count,
            "error_count": self._summary.error_count
        }

ocr_monitoring = OCRMonitoring()
