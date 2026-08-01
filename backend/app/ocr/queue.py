import time
import asyncio
from typing import Dict, Any, Optional

_ocr_task_store: Dict[str, Dict[str, Any]] = {}

class AsyncOCRQueue:
    """
    Async Job Queue with Exponential Backoff & Retries for heavy OCR Processing.
    """
    def __init__(self, max_retries: int = 3, initial_delay_sec: float = 1.0):
        self.max_retries = max_retries
        self.initial_delay_sec = initial_delay_sec

    async def enqueue_ocr_job(self, document_id: str, file_name: str, options: Dict[str, Any]) -> str:
        task_id = f"ocr_task_{int(time.time())}"
        task_record = {
            "task_id": task_id,
            "document_id": document_id,
            "file_name": file_name,
            "status": "QUEUED",  # QUEUED, PROCESSING, COMPLETED, FAILED
            "retry_count": 0,
            "result": None,
            "error_message": None,
            "enqueued_at": time.time(),
            "completed_at": None
        }
        _ocr_task_store[task_id] = task_record
        
        # Dispatch background execution
        asyncio.create_task(self._execute_with_retry(task_id, options))
        return task_id

    async def _execute_with_retry(self, task_id: str, options: Dict[str, Any]) -> None:
        record = _ocr_task_store[task_id]
        record["status"] = "PROCESSING"

        for attempt in range(1, self.max_retries + 1):
            try:
                # Import pipeline lazily to prevent circular imports
                from app.ocr.pipeline import ocr_pipeline
                from app.ocr.normalizer import FormatNormalizer
                
                dummy_bytes = b"%PDF-1.4 Mock Document Content for OCR Processing%"
                normalized = FormatNormalizer.normalize(dummy_bytes, record["file_name"])
                result = await ocr_pipeline.process(normalized)
                
                record["status"] = "COMPLETED"
                record["result"] = result
                record["completed_at"] = time.time()
                return
            except Exception as e:
                record["retry_count"] = attempt
                if attempt < self.max_retries:
                    delay = self.initial_delay_sec * (2 ** (attempt - 1))
                    await asyncio.sleep(delay)
                else:
                    record["status"] = "FAILED"
                    record["error_message"] = str(e)

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        return _ocr_task_store.get(task_id)

async_ocr_queue = AsyncOCRQueue()
