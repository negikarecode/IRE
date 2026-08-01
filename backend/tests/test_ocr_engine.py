import pytest
import asyncio
from fastapi.testclient import TestClient
from app.main import app
from app.ocr.format_converters import format_converter
from app.ocr.pipeline import ocr_pipeline
from app.ocr.queue import async_ocr_queue

def test_ocr_format_converter():
    fake_png_bytes = b"sample_png_bytes"
    pages = format_converter.convert(fake_png_bytes, "sample.png")
    assert len(pages) == 1
    assert pages[0].page_number == 1
    assert pages[0].image_bytes == fake_png_bytes

def test_ocr_pipeline_processing():
    async def run():
        fake_doc_bytes = b"Sample Medical Discharge Document\nDiagnosis: Hypertension"
        output = await ocr_pipeline.process("discharge.pdf", fake_doc_bytes)
        assert output["document_metadata"]["file_name"] == "discharge.pdf"
        assert output["confidence_scores"]["overall_confidence"] > 0.0
        assert "full_text" in output["extraction"]
    asyncio.run(run())

def test_ocr_async_queue():
    async def run():
        task_id = await async_ocr_queue.enqueue_ocr_job("doc_test_100", "test_report.pdf", {})
        assert task_id is not None
        assert task_id.startswith("ocr_task_")
        
        status_info = async_ocr_queue.get_task_status(task_id)
        assert status_info is not None
        assert status_info["status"] in ["QUEUED", "PROCESSING", "COMPLETED"]
    asyncio.run(run())

def test_ocr_extract_endpoint():
    with TestClient(app) as test_c:
        files = {"file": ("test_lab.png", b"Sample Lab Data WBC 6.5", "image/png")}
        res = test_c.post("/api/v1/ocr/extract", files=files)
        assert res.status_code == 200
        res_json = res.json()
        assert res_json["success"] is True
        assert res_json["data"]["document_metadata"]["file_name"] == "test_lab.png"
