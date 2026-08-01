import asyncio
from dataclasses import dataclass
from typing import Callable, Any, Dict
import uuid

@dataclass
class InferenceJob:
    job_id: str
    tenant_id: str
    prompt: str
    status: str  # QUEUED, PROCESSING, COMPLETED, FAILED
    result: Any = None
    error: str = None

class InferenceQueue:
    """
    In-memory / Redis asynchronous inference request queue.
    """
    def __init__(self):
        self._jobs: Dict[str, InferenceJob] = {}

    async def enqueue(self, tenant_id: str, prompt: str) -> str:
        job_id = f"job_{uuid.uuid4().hex[:8]}"
        job = InferenceJob(job_id=job_id, tenant_id=tenant_id, prompt=prompt, status="QUEUED")
        self._jobs[job_id] = job
        return job_id

    async def get_status(self, job_id: str) -> InferenceJob:
        return self._jobs.get(job_id)

inference_queue = InferenceQueue()
