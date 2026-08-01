from typing import Dict, Any, List

class OCRJSONFormatter:
    """
    Standardized JSON Output Generator for OCR Service.
    Zero insurance rules. Pure structural document extraction schema.
    """
    def format_output(
        self,
        file_name: str,
        detected_language: str,
        enhancement_meta: Dict[str, Any],
        full_text: str,
        layout_blocks: List[Any],
        extracted_tables: List[Any],
        confidence_metrics: Dict[str, float]
    ) -> Dict[str, Any]:
        return {
            "document_metadata": {
                "file_name": file_name,
                "detected_language": detected_language,
                "preprocessing": enhancement_meta
            },
            "extraction": {
                "full_text": full_text,
                "layout_blocks": [
                    {
                        "block_id": b.block_id,
                        "type": b.block_type,
                        "bounding_box": b.bounding_box,
                        "confidence": b.confidence
                    }
                    for b in layout_blocks
                ],
                "tables": [
                    {
                        "table_id": t.table_id,
                        "row_count": t.row_count,
                        "column_count": t.column_count,
                        "headers": t.headers,
                        "matrix": t.matrix
                    }
                    for t in extracted_tables
                ]
            },
            "confidence_scores": confidence_metrics
        }

json_formatter = OCRJSONFormatter()
