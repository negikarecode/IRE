from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timezone

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.infrastructure.db.models.claim import JobModel, JobStatus, JobType
from app.infrastructure.services.job_queue_service import JobQueueService

router = APIRouter()


# Pydantic Models
class JobResponse(BaseModel):
    id: str
    hospital_id: str
    job_type: str
    status: str
    document_id: Optional[str] = None
    claim_id: Optional[str] = None
    retry_count: int
    max_retries: int
    queued_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    processing_time_seconds: Optional[float] = None
    error_message: Optional[str] = None
    result: Optional[dict] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class JobCreateRequest(BaseModel):
    job_type: str
    document_id: Optional[str] = None
    claim_id: Optional[str] = None
    payload: Optional[dict] = None
    max_retries: int = 3


class JobStatisticsResponse(BaseModel):
    total: int
    queued: int
    running: int
    completed: int
    failed: int
    cancelled: int
    retrying: int
    average_processing_time_seconds: float


from app.core.exceptions import NotFoundException, ForbiddenException, BadRequestException

# API Endpoints
@router.get("", status_code=200)
async def get_jobs(
    status: Optional[str] = Query(None, description="Filter by job status"),
    job_type: Optional[str] = Query(None, description="Filter by job type"),
    document_id: Optional[str] = Query(None, description="Filter by document ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get jobs for the authenticated user's hospital.
    """
    hospital_id = getattr(current_user, "hospital_id", current_user.get("hospital_id") if isinstance(current_user, dict) else None)
    
    query = db.query(JobModel).filter(JobModel.hospital_id == hospital_id)
    
    if status:
        query = query.filter(JobModel.status == status)
    if job_type:
        query = query.filter(JobModel.job_type == job_type)
    if document_id:
        query = query.filter(JobModel.document_id == document_id)
    
    jobs = query.order_by(JobModel.queued_at.desc()).offset(skip).limit(limit).all()
    data = [JobResponse.model_validate(j).model_dump() for j in jobs]
    return {
        "success": True,
        "message": "Jobs retrieved successfully",
        "data": data
    }


@router.get("/{job_id}", status_code=200)
async def get_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get a specific job by ID.
    """
    hospital_id = getattr(current_user, "hospital_id", current_user.get("hospital_id") if isinstance(current_user, dict) else None)
    
    job_service = JobQueueService(db)
    job = job_service.get_job(job_id)
    
    if not job:
        raise NotFoundException(message="Job not found")
    
    if job.hospital_id != hospital_id:
        raise ForbiddenException(message="Access denied")
    
    data = JobResponse.model_validate(job)
    return {
        "success": True,
        "message": "Job details retrieved successfully",
        "data": data.model_dump()
    }


@router.post("", status_code=201)
async def create_job(
    job_request: JobCreateRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Create a new job in the queue.
    """
    hospital_id = getattr(current_user, "hospital_id", current_user.get("hospital_id") if isinstance(current_user, dict) else None)
    user_id = getattr(current_user, "id", current_user.get("user_id", "usr_1") if isinstance(current_user, dict) else "usr_1")
    
    try:
        job_type = JobType(job_request.job_type)
    except ValueError:
        raise BadRequestException(message=f"Invalid job type: {job_request.job_type}")
    
    job_service = JobQueueService(db)
    job = job_service.create_job(
        hospital_id=hospital_id,
        job_type=job_type,
        payload=job_request.payload,
        document_id=job_request.document_id,
        claim_id=job_request.claim_id,
        created_by=user_id,
        max_retries=job_request.max_retries
    )
    
    data = JobResponse.model_validate(job)
    return {
        "success": True,
        "message": "Job created successfully",
        "data": data.model_dump()
    }


@router.post("/{job_id}/cancel", status_code=200)
async def cancel_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Cancel a running or queued job.
    """
    hospital_id = getattr(current_user, "hospital_id", current_user.get("hospital_id") if isinstance(current_user, dict) else None)
    
    job_service = JobQueueService(db)
    job = job_service.get_job(job_id)
    
    if not job:
        raise NotFoundException(message="Job not found")
    
    if job.hospital_id != hospital_id:
        raise ForbiddenException(message="Access denied")
    
    cancelled_job = job_service.cancel_job(job_id)
    
    if not cancelled_job:
        raise BadRequestException(message="Job cannot be cancelled")
    
    data = JobResponse.model_validate(cancelled_job)
    return {
        "success": True,
        "message": "Job cancelled successfully",
        "data": data.model_dump()
    }


@router.get("/statistics/overview", status_code=200)
async def get_job_statistics(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get job statistics for the authenticated user's hospital.
    """
    hospital_id = getattr(current_user, "hospital_id", current_user.get("hospital_id") if isinstance(current_user, dict) else None)
    
    job_service = JobQueueService(db)
    stats = job_service.get_job_statistics(hospital_id)
    
    data = JobStatisticsResponse(**stats)
    return {
        "success": True,
        "message": "Job statistics retrieved successfully",
        "data": data.model_dump()
    }


@router.get("/document/{document_id}", status_code=200)
async def get_document_jobs(
    document_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get all jobs for a specific document.
    """
    hospital_id = getattr(current_user, "hospital_id", current_user.get("hospital_id") if isinstance(current_user, dict) else None)
    
    job_service = JobQueueService(db)
    jobs = job_service.get_jobs_by_document(document_id)
    
    filtered_jobs = [job for job in jobs if job.hospital_id == hospital_id]
    data = [JobResponse.model_validate(j).model_dump() for j in filtered_jobs]
    
    return {
        "success": True,
        "message": "Document jobs retrieved successfully",
        "data": data
    }


@router.post("/retry/failed", status_code=200)
async def retry_failed_jobs(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Manually trigger retry of failed jobs that are eligible for retry.
    """
    hospital_id = getattr(current_user, "hospital_id", current_user.get("hospital_id") if isinstance(current_user, dict) else None)
    
    job_service = JobQueueService(db)
    failed_jobs = job_service.get_failed_jobs_for_retry()
    
    hospital_failed_jobs = [job for job in failed_jobs if job.hospital_id == hospital_id]
    
    retried_count = 0
    for job in hospital_failed_jobs:
        try:
            if job.job_type == JobType.OCR.value:
                from app.infrastructure.tasks.ocr_tasks import process_document_ocr_task
                payload = job.payload or {}
                document_id = payload.get('document_id')
                file_path = payload.get('file_path')
                
                if document_id and file_path:
                    job_service.increment_retry(job.id)
                    process_document_ocr_task.delay(document_id, hospital_id, file_path, job.id)
                    retried_count += 1
        except Exception:
            pass
    
    return {
        "success": True,
        "message": f"Retried {retried_count} failed jobs",
        "data": {
            "retried_count": retried_count
        }
    }
