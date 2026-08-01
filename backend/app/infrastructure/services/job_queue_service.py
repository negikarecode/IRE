from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from app.infrastructure.db.models.claim import JobModel, JobStatus, JobType
from app.core.database import get_db


class JobQueueService:
    """Service for managing background job queue with Celery integration"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_job(
        self,
        hospital_id: str,
        job_type: JobType,
        payload: Optional[Dict[str, Any]] = None,
        document_id: Optional[str] = None,
        claim_id: Optional[str] = None,
        created_by: Optional[str] = None,
        max_retries: int = 3
    ) -> JobModel:
        """Create a new job in the queue"""
        job = JobModel(
            hospital_id=hospital_id,
            job_type=job_type.value,
            status=JobStatus.QUEUED.value,
            payload=payload,
            document_id=document_id,
            claim_id=claim_id,
            created_by=created_by,
            max_retries=max_retries,
            queued_at=datetime.now(timezone.utc)
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job
    
    def update_job_status(
        self,
        job_id: str,
        status: JobStatus,
        result: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None
    ) -> Optional[JobModel]:
        """Update job status and timing"""
        job = self.db.query(JobModel).filter(JobModel.id == job_id).first()
        if not job:
            return None
        
        job.status = status.value
        job.updated_at = datetime.now(timezone.utc)
        
        if status == JobStatus.RUNNING and not job.started_at:
            job.started_at = datetime.now(timezone.utc)
        elif status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
            job.completed_at = datetime.now(timezone.utc)
            if job.started_at:
                processing_time = (job.completed_at - job.started_at).total_seconds()
                job.processing_time_seconds = processing_time
        
        if result:
            job.result = result
        if error_message:
            job.error_message = error_message
        
        self.db.commit()
        self.db.refresh(job)
        return job
    
    def increment_retry(self, job_id: str) -> Optional[JobModel]:
        """Increment retry count for a failed job"""
        job = self.db.query(JobModel).filter(JobModel.id == job_id).first()
        if not job:
            return None
        
        job.retry_count += 1
        job.status = JobStatus.RETRYING.value
        job.updated_at = datetime.now(timezone.utc)
        
        self.db.commit()
        self.db.refresh(job)
        return job
    
    def cancel_job(self, job_id: str) -> Optional[JobModel]:
        """Cancel a running or queued job"""
        job = self.db.query(JobModel).filter(JobModel.id == job_id).first()
        if not job:
            return None
        
        if job.status in [JobStatus.QUEUED.value, JobStatus.RUNNING.value, JobStatus.RETRYING.value]:
            job.status = JobStatus.CANCELLED.value
            job.completed_at = datetime.now(timezone.utc)
            job.updated_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(job)
        
        return job
    
    def get_job(self, job_id: str) -> Optional[JobModel]:
        """Get a job by ID"""
        return self.db.query(JobModel).filter(JobModel.id == job_id).first()
    
    def get_jobs_by_document(self, document_id: str) -> List[JobModel]:
        """Get all jobs for a specific document"""
        return self.db.query(JobModel).filter(JobModel.document_id == document_id).all()
    
    def get_jobs_by_hospital(self, hospital_id: str, status: Optional[JobStatus] = None) -> List[JobModel]:
        """Get jobs for a hospital, optionally filtered by status"""
        query = self.db.query(JobModel).filter(JobModel.hospital_id == hospital_id)
        if status:
            query = query.filter(JobModel.status == status.value)
        return query.order_by(JobModel.queued_at.desc()).all()
    
    def get_queued_jobs(self, job_type: Optional[JobType] = None, limit: int = 10) -> List[JobModel]:
        """Get queued jobs ready for processing"""
        query = self.db.query(JobModel).filter(JobModel.status == JobStatus.QUEUED.value)
        if job_type:
            query = query.filter(JobModel.job_type == job_type.value)
        return query.order_by(JobModel.queued_at.asc()).limit(limit).all()
    
    def get_failed_jobs_for_retry(self, max_age_minutes: int = 5) -> List[JobModel]:
        """Get failed jobs that can be retried"""
        from datetime import timedelta
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=max_age_minutes)
        
        return self.db.query(JobModel).filter(
            JobModel.status == JobStatus.FAILED.value,
            JobModel.retry_count < JobModel.max_retries,
            JobModel.completed_at < cutoff_time
        ).all()
    
    def get_job_statistics(self, hospital_id: str) -> Dict[str, Any]:
        """Get job statistics for a hospital"""
        jobs = self.get_jobs_by_hospital(hospital_id)
        
        total = len(jobs)
        queued = len([j for j in jobs if j.status == JobStatus.QUEUED.value])
        running = len([j for j in jobs if j.status == JobStatus.RUNNING.value])
        completed = len([j for j in jobs if j.status == JobStatus.COMPLETED.value])
        failed = len([j for j in jobs if j.status == JobStatus.FAILED.value])
        cancelled = len([j for j in jobs if j.status == JobStatus.CANCELLED.value])
        retrying = len([j for j in jobs if j.status == JobStatus.RETRYING.value])
        
        # Calculate average processing time for completed jobs
        completed_jobs = [j for j in jobs if j.status == JobStatus.COMPLETED.value and j.processing_time_seconds]
        avg_processing_time = (
            sum(j.processing_time_seconds for j in completed_jobs) / len(completed_jobs)
            if completed_jobs else 0
        )
        
        return {
            "total": total,
            "queued": queued,
            "running": running,
            "completed": completed,
            "failed": failed,
            "cancelled": cancelled,
            "retrying": retrying,
            "average_processing_time_seconds": avg_processing_time
        }
    
    def cleanup_old_jobs(self, days_to_keep: int = 30) -> int:
        """Delete completed jobs older than specified days"""
        from datetime import timedelta
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_to_keep)
        
        deleted = self.db.query(JobModel).filter(
            JobModel.status == JobStatus.COMPLETED.value,
            JobModel.completed_at < cutoff_date
        ).delete()
        
        self.db.commit()
        return deleted
