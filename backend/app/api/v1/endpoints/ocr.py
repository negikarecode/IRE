import os
from fastapi import APIRouter, UploadFile, File, Form, status
from typing import Optional, Dict, Any
from app.core.exceptions import BadRequestException, NotFoundException
from app.ocr.format_converters import format_converter
from app.ocr.pipeline import ocr_pipeline
from app.ocr.queue import async_ocr_queue
from app.ocr.monitoring import ocr_monitoring

ALLOWED_OCR_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".tiff", ".tif"}
MAX_OCR_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

router = APIRouter()

@router.post("/extract", status_code=status.HTTP_200_OK)
async def extract_document_ocr(
    file: UploadFile = File(...)
):
    """
    Synchronous Document OCR Extraction Endpoint.
    Extracts text, handwriting, language, layout regions, bounding boxes, tables, and confidence scores into standardized JSON.
    """
    filename = file.filename or "doc.png"
    ext = os.path.splitext(filename)[1].lower()
    if ext and ext not in ALLOWED_OCR_EXTENSIONS:
        raise BadRequestException(message=f"Disallowed file extension '{ext}'. Allowed: PDF, JPG, JPEG, PNG, TIFF")

    chunks = []
    file_size = 0
    CHUNK_SIZE = 64 * 1024
    
    while True:
        chunk = await file.read(CHUNK_SIZE)
        if not chunk:
            break
        file_size += len(chunk)
        if file_size > MAX_OCR_FILE_SIZE:
            raise BadRequestException(message="File size exceeds maximum limit of 50 MB.")
        chunks.append(chunk)
        
    contents = b"".join(chunks)
    if not contents:
        raise BadRequestException(message="Uploaded file is empty.")

    try:
        pages = format_converter.convert(contents, filename)
        output = await ocr_pipeline.process(filename, contents)
        return {
            "success": True,
            "message": "OCR extraction completed successfully",
            "data": output
        }
    except Exception as e:
        raise BadRequestException(message=f"OCR Extraction failed: {str(e)}")

@router.post("/async_extract", status_code=status.HTTP_202_ACCEPTED)
async def async_extract_document_ocr(
    file: UploadFile = File(...),
    document_id: Optional[str] = Form(None)
):
    """
    Asynchronous Document OCR Job Submission Endpoint.
    Enqueues OCR job in background queue with exponential backoff & retries.
    """
    filename = file.filename or "doc.png"
    ext = os.path.splitext(filename)[1].lower()
    if ext and ext not in ALLOWED_OCR_EXTENSIONS:
        raise BadRequestException(message=f"Disallowed file extension '{ext}'. Allowed: PDF, JPG, JPEG, PNG, TIFF")

    contents = await file.read()
    if not contents:
        raise BadRequestException(message="Uploaded file is empty.")
    if len(contents) > MAX_OCR_FILE_SIZE:
        raise BadRequestException(message="File size exceeds maximum limit of 50 MB.")

    doc_id = document_id or f"doc_{file.filename}"
    task_id = await async_ocr_queue.enqueue_ocr_job(doc_id, file.filename or "doc.png", {})

    return {
        "success": True,
        "message": "OCR job enqueued successfully",
        "data": {
            "status": "ENQUEUED",
            "task_id": task_id,
            "document_id": doc_id,
            "poll_url": f"/api/v1/ocr/tasks/{task_id}"
        }
    }

@router.get("/tasks/{task_id}", status_code=status.HTTP_200_OK)
async def get_ocr_task_status(task_id: str):
    """
    Poll Async OCR Task Status and Results.
    """
    task = async_ocr_queue.get_task_status(task_id)
    if not task:
        raise NotFoundException(message=f"Task '{task_id}' not found.")
    return {
        "success": True,
        "message": "Task status retrieved successfully",
        "data": task
    }

@router.get("/monitoring", status_code=status.HTTP_200_OK)
async def get_ocr_monitoring_metrics():
    """
    Retrieve OCR Processing Telemetry & Monitoring Metrics.
    """
    return {
        "success": True,
        "message": "OCR monitoring metrics retrieved successfully",
        "data": ocr_monitoring.get_metrics()
    }
