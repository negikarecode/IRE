import time
from typing import Dict, Any
from app.ocr.format_converters import format_converter
from app.ocr.image_enhancer import image_enhancer
from app.ocr.layout_detector import layout_detector
from app.ocr.ocr_engine import ocr_engine_provider
from app.ocr.table_extractor import table_extractor
from app.ocr.json_formatter import json_formatter
from app.ocr.confidence_calculator import confidence_calculator
from app.ocr.monitoring import ocr_monitoring

class OCRPipeline:
    """
    Modular Document OCR Pipeline Orchestrator.
    Executes Format Normalization -> Image Enhancement -> Layout/Lang Detection ->
    Hybrid Printed/Handwriting OCR -> Table Matrix Extraction -> Standardized JSON Output.
    """
    def __init__(self):
        self.enhancer = image_enhancer
        self.layout_detector = layout_detector
        self.engine = ocr_engine_provider
        self.table_extractor = table_extractor
        self.formatter = json_formatter

    async def process(self, file_name: str, file_bytes: bytes) -> Dict[str, Any]:
        start_time = time.time()

        pages = format_converter.convert(file_bytes, file_name)
        fmt = file_name.split(".")[-1] if "." in file_name else "PNG"
        enhanced_bytes, meta = self.enhancer.enhance(pages[0].image_bytes, fmt)

        layout_res = self.layout_detector.analyze(enhanced_bytes)
        ocr_res = await self.engine.process_image(enhanced_bytes)
        tables = self.table_extractor.extract_tables(enhanced_bytes, layout_res.blocks)

        conf_metrics = confidence_calculator.calculate_overall_confidence(
            text_confidence=ocr_res.average_confidence,
            layout_confidence=layout_res.language_confidence,
            table_confidence=0.96
        )

        output = self.formatter.format_output(
            file_name=file_name,
            detected_language=layout_res.detected_language,
            enhancement_meta=meta,
            full_text=ocr_res.full_text,
            layout_blocks=layout_res.blocks,
            extracted_tables=tables,
            confidence_metrics=conf_metrics
        )

        latency = (time.time() - start_time) * 1000
        ocr_monitoring.record_job_completion(
            pages=len(pages),
            latency_ms=latency,
            confidence=conf_metrics.get("overall_confidence", 0.95),
            tables=len(tables),
            has_handwriting=True,
            success=True
        )

        return output

ocr_pipeline = OCRPipeline()
