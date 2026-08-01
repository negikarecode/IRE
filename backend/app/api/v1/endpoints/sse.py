from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import AsyncGenerator, Optional
import asyncio
import json
from datetime import datetime, timezone

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.exceptions import UnauthorizedException
from app.infrastructure.db.models.claim import JobModel, JobStatus

router = APIRouter()


async def job_status_generator(
    hospital_id: str,
    db: Session,
    document_id: Optional[str] = None
) -> AsyncGenerator[str, None]:
    """
    Generator function that yields SSE events for job status updates.
    """
    last_status = None
    
    while True:
        try:
            # Build query
            query = db.query(JobModel).filter(JobModel.hospital_id == hospital_id)
            if document_id:
                query = query.filter(JobModel.document_id == document_id)
            
            # Get recent jobs
            jobs = query.order_by(JobModel.updated_at.desc()).limit(10).all()
            
            # Check for status changes
            for job in jobs:
                job_data = {
                    "id": job.id,
                    "job_type": job.job_type,
                    "status": job.status,
                    "document_id": job.document_id,
                    "retry_count": job.retry_count,
                    "processing_time_seconds": job.processing_time_seconds,
                    "error_message": job.error_message,
                    "updated_at": job.updated_at.isoformat() if job.updated_at else None
                }
                
                # Send event if status changed or new job
                status_key = f"{job.id}_{job.status}"
                if status_key != last_status:
                    event_data = {
                        "event": "job_update",
                        "data": job_data,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                    yield f"data: {json.dumps(event_data)}\n\n"
                    last_status = status_key
            
            # Send heartbeat every 10 seconds
            yield f"data: {json.dumps({'event': 'heartbeat', 'timestamp': datetime.now(timezone.utc).isoformat()})}\n\n"
            
            # Wait before next check
            await asyncio.sleep(2)
            
        except Exception as e:
            error_data = {
                "event": "error",
                "data": {"message": str(e)},
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            yield f"data: {json.dumps(error_data)}\n\n"
            await asyncio.sleep(5)


@router.get("/jobs/stream")
async def stream_job_updates(
    document_id: str = None,
    token: str = None,
    db: Session = Depends(get_db)
):
    """
    SSE endpoint for real-time job status updates.
    
    Clients can subscribe to this endpoint to receive real-time updates
    about job status changes without polling.
    
    Note: Token is passed as query parameter since EventSource doesn't support custom headers.
    """
    # Validate token (simplified - in production use proper JWT validation)
    if not token:
        raise UnauthorizedException(message="Authentication required")
    
    # For now, extract hospital_id from token (in production, decode JWT properly)
    # This is a simplified version - implement proper JWT validation
    hospital_id = "default_hospital"  # Replace with actual token validation
    
    return StreamingResponse(
        job_status_generator(hospital_id, document_id, db),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )
