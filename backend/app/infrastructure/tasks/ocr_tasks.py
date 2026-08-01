import logging
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update

from app.core.celery_app import celery_app
from app.core.database import get_db
from app.infrastructure.db.models.claim import DocumentModel, OCRResultModel, ClinicalExtractionModel, ProcessingStatus, JobModel, JobStatus, JobType
from app.infrastructure.services.ocr_service import ocr_service
from app.infrastructure.services.classification_service import classification_service
from app.infrastructure.services.clinical_extraction_service import clinical_extraction_service
from app.infrastructure.services.job_queue_service import JobQueueService

logger = logging.getLogger("ocr_tasks")


@celery_app.task(bind=True, name="process_document_ocr", max_retries=3)
def process_document_ocr_task(self, document_id: str, hospital_id: str, file_path: str, job_id: str = None):
    """
    Async Celery task to process document OCR with job queue integration.
    
    Args:
        document_id: ID of the document to process
        hospital_id: ID of the hospital owning the document
        file_path: Path to the document file
        job_id: Optional job ID for tracking
    """
    logger.info(f"[OCR_TASK_START] Document ID: {document_id}, Hospital ID: {hospital_id}, Job ID: {job_id}")
    
    # Create synchronous database session for Celery task
    from app.core.database import DATABASE_URL
    engine = create_async_engine(DATABASE_URL.replace('+aiosqlite', ''))
    
    # Initialize job queue service if job_id provided
    job_service = None
    if job_id:
        try:
            with engine.connect() as conn:
                job_service = JobQueueService(conn)
                job_service.update_job_status(job_id, JobStatus.RUNNING)
        except Exception as e:
            logger.error(f"[JOB_QUEUE_ERROR] Failed to update job status: {e}")
    
    try:
        # Update document status to processing
        with engine.connect() as conn:
            conn.execute(
                update(DocumentModel)
                .where(DocumentModel.id == document_id)
                .values(processing_status=ProcessingStatus.PROCESSING.value)
            )
            conn.commit()
        
        # Create OCR result record
        ocr_result_id = str(__import__('uuid').uuid4())
        with engine.connect() as conn:
            conn.execute(
                update(OCRResultModel.__table__)
                .values(
                    processing_status=ProcessingStatus.PROCESSING.value,
                    started_at=datetime.now(timezone.utc)
                )
            )
            conn.commit()
        
        # Perform OCR processing
        ocr_results = ocr_service.process_document(file_path, document_id, hospital_id)
        
        # Perform document classification if OCR succeeded
        if ocr_results['processing_status'] == 'completed' and ocr_results['raw_text']:
            logger.info(f"[CLASSIFICATION_START] Document ID: {document_id}")
            
            # Get document filename for classification
            from app.core.database import DATABASE_URL
            with engine.connect() as conn:
                result = conn.execute(
                    select(DocumentModel).where(DocumentModel.id == document_id)
                )
                document = result.fetchone()
                filename = document.original_filename if document else ""
            
            # Classify document
            doc_type, confidence = classification_service.classify_document(
                ocr_results['raw_text'], 
                filename
            )
            
            logger.info(f"[CLASSIFICATION_RESULT] Document ID: {document_id}, Type: {doc_type}, Confidence: {confidence:.2f}")
            
            ocr_results['document_type'] = doc_type
            ocr_results['classification_confidence'] = confidence
        else:
            ocr_results['document_type'] = 'unknown'
            ocr_results['classification_confidence'] = 0.0
        
        # Perform clinical data extraction if OCR succeeded
        ocr_results['clinical_data'] = None
        
        # Update document with OCR results
        with engine.connect() as conn:
            # Update document
            conn.execute(
                update(DocumentModel)
                .where(DocumentModel.id == document_id)
                .values(
                    processing_status=ocr_results['processing_status'],
                    pages=ocr_results['page_count'],
                    document_type=ocr_results['document_type'],
                    classification_confidence=ocr_results['classification_confidence'],
                    is_manually_classified=0  # Auto-classified
                )
            )
            
            # Create or update OCR result
            if ocr_results['processing_status'] == 'completed':
                conn.execute(
                    update(OCRResultModel.__table__)
                    .where(OCRResultModel.document_id == document_id)
                    .values(
                        raw_text=ocr_results['raw_text'],
                        structured_data=ocr_results['structured_data'],
                        ocr_confidence=ocr_results['ocr_confidence'],
                        processing_time_seconds=ocr_results['processing_time_seconds'],
                        page_count=ocr_results['page_count'],
                        detected_language=ocr_results['detected_language'],
                        processing_status=ProcessingStatus.COMPLETED.value,
                        error_message=None,
                        completed_at=datetime.now(timezone.utc)
                    )
                )
                
                # Perform clinical data extraction with normalization
                if ocr_results['raw_text']:
                    logger.info(f"[CLINICAL_EXTRACTION_START] Document ID: {document_id}")
                    
                    # Extract clinical data with normalization
                    clinical_data = clinical_extraction_service.extract_clinical_data(
                        ocr_results['raw_text'],
                        document_id=document_id,
                        hospital_id=hospital_id,
                        db=conn  # Pass database connection for normalization storage
                    )
                    
                    logger.info(f"[CLINICAL_EXTRACTION_RESULT] Document ID: {document_id}, Confidence: {clinical_data['extraction_confidence']:.2f}")
                    
                    ocr_results['clinical_data'] = clinical_data
                
                # Store clinical extraction results
                if ocr_results['clinical_data']:
                    clinical_data = ocr_results['clinical_data']
                    
                    # Check if extraction already exists
                    existing = conn.execute(
                        select(ClinicalExtractionModel).where(ClinicalExtractionModel.document_id == document_id)
                    ).fetchone()
                    
                    if existing:
                        # Update existing extraction
                        conn.execute(
                            update(ClinicalExtractionModel.__table__)
                            .where(ClinicalExtractionModel.document_id == document_id)
                            .values(
                                patient_name=clinical_data.get('patient_name'),
                                uhid=clinical_data.get('uhid'),
                                mrn=clinical_data.get('mrn'),
                                age=clinical_data.get('age'),
                                gender=clinical_data.get('gender'),
                                admission_date=clinical_data.get('admission_date'),
                                discharge_date=clinical_data.get('discharge_date'),
                                operation_date=clinical_data.get('operation_date'),
                                length_of_stay=clinical_data.get('length_of_stay'),
                                hospital=clinical_data.get('hospital'),
                                doctor=clinical_data.get('doctor'),
                                department=clinical_data.get('department'),
                                diagnosis=clinical_data.get('diagnosis'),
                                icd_codes=clinical_data.get('icd_codes'),
                                procedure=clinical_data.get('procedure'),
                                cpt_codes=clinical_data.get('cpt_codes'),
                                medicines=clinical_data.get('medicines'),
                                implants=clinical_data.get('implants'),
                                insurance_company=clinical_data.get('insurance_company'),
                                policy_number=clinical_data.get('policy_number'),
                                bill_amount=clinical_data.get('bill_amount'),
                                invoice_number=clinical_data.get('invoice_number'),
                                extraction_confidence=clinical_data.get('extraction_confidence'),
                                extraction_timestamp=datetime.now(timezone.utc)
                            )
                        )
                    else:
                        # Create new extraction
                        extraction_id = str(__import__('uuid').uuid4())
                        conn.execute(
                            ClinicalExtractionModel.__table__.insert().values(
                                id=extraction_id,
                                document_id=document_id,
                                hospital_id=hospital_id,
                                patient_name=clinical_data.get('patient_name'),
                                uhid=clinical_data.get('uhid'),
                                mrn=clinical_data.get('mrn'),
                                age=clinical_data.get('age'),
                                gender=clinical_data.get('gender'),
                                admission_date=clinical_data.get('admission_date'),
                                discharge_date=clinical_data.get('discharge_date'),
                                operation_date=clinical_data.get('operation_date'),
                                length_of_stay=clinical_data.get('length_of_stay'),
                                hospital=clinical_data.get('hospital'),
                                doctor=clinical_data.get('doctor'),
                                department=clinical_data.get('department'),
                                diagnosis=clinical_data.get('diagnosis'),
                                icd_codes=clinical_data.get('icd_codes'),
                                procedure=clinical_data.get('procedure'),
                                cpt_codes=clinical_data.get('cpt_codes'),
                                medicines=clinical_data.get('medicines'),
                                implants=clinical_data.get('implants'),
                                insurance_company=clinical_data.get('insurance_company'),
                                policy_number=clinical_data.get('policy_number'),
                                bill_amount=clinical_data.get('bill_amount'),
                                invoice_number=clinical_data.get('invoice_number'),
                                extraction_confidence=clinical_data.get('extraction_confidence'),
                                extraction_timestamp=datetime.now(timezone.utc),
                                created_at=datetime.now(timezone.utc)
                            )
                        )
            else:
                conn.execute(
                    update(OCRResultModel.__table__)
                    .where(OCRResultModel.document_id == document_id)
                    .values(
                        processing_status=ProcessingStatus.FAILED.value,
                        error_message=ocr_results['error_message'],
                        completed_at=datetime.now(timezone.utc)
                    )
                )
            
            conn.commit()
        
        logger.info(f"[OCR_TASK_SUCCESS] Document ID: {document_id}, Status: {ocr_results['processing_status']}")
        
        # Update job status to completed if job_id provided
        if job_service and job_id:
            try:
                job_service.update_job_status(
                    job_id, 
                    JobStatus.COMPLETED, 
                    result={
                        'document_id': document_id,
                        'status': ocr_results['processing_status'],
                        'page_count': ocr_results['page_count'],
                        'confidence': ocr_results['ocr_confidence'],
                        'processing_time': ocr_results['processing_time_seconds']
                    }
                )
            except Exception as e:
                logger.error(f"[JOB_QUEUE_ERROR] Failed to update job completion status: {e}")
        
        return {
            'document_id': document_id,
            'status': ocr_results['processing_status'],
            'page_count': ocr_results['page_count'],
            'confidence': ocr_results['ocr_confidence'],
            'processing_time': ocr_results['processing_time_seconds']
        }
        
    except Exception as e:
        logger.error(f"[OCR_TASK_ERROR] Document ID: {document_id}, Error: {str(e)}")
        
        # Update job status to failed if job_id provided
        if job_service and job_id:
            try:
                job_service.update_job_status(
                    job_id, 
                    JobStatus.FAILED, 
                    error_message=str(e)
                )
                # Increment retry count if under max retries
                job = job_service.get_job(job_id)
                if job and job.retry_count < job.max_retries:
                    job_service.increment_retry(job_id)
                    # Retry with exponential backoff
                    raise self.retry(countdown=60 * (2 ** job.retry_count))
            except Exception as job_error:
                logger.error(f"[JOB_QUEUE_ERROR] Failed to update job failure status: {job_error}")
        
        # Update status to failed
        try:
            with engine.connect() as conn:
                conn.execute(
                    update(DocumentModel)
                    .where(DocumentModel.id == document_id)
                    .values(processing_status=ProcessingStatus.FAILED.value)
                )
                conn.execute(
                    update(OCRResultModel.__table__)
                    .where(OCRResultModel.document_id == document_id)
                    .values(
                        processing_status=ProcessingStatus.FAILED.value,
                        error_message=str(e),
                        completed_at=datetime.now(timezone.utc)
                    )
                )
                conn.commit()
        except Exception as db_error:
            logger.error(f"[OCR_TASK_DB_ERROR] Failed to update error status: {db_error}")
        
        raise e


def trigger_ocr_processing(document_id: str, hospital_id: str, file_path: str, created_by: str = None) -> str:
    """
    Trigger OCR processing for a document with job queue integration.
    
    Args:
        document_id: ID of the document to process
        hospital_id: ID of the hospital owning the document
        file_path: Path to the document file
        created_by: User ID who triggered the processing
    
    Returns:
        Job ID for tracking
    """
    logger.info(f"[OCR_TRIGGER] Document ID: {document_id}")
    
    # Create synchronous database session
    from app.core.database import DATABASE_URL
    engine = create_async_engine(DATABASE_URL.replace('+aiosqlite', ''))
    
    # Create OCR result record
    ocr_result_id = str(__import__('uuid').uuid4())
    
    try:
        with engine.connect() as conn:
            conn.execute(
                OCRResultModel.__table__.insert().values(
                    id=ocr_result_id,
                    document_id=document_id,
                    hospital_id=hospital_id,
                    processing_status=ProcessingStatus.PENDING.value,
                    created_at=datetime.now(timezone.utc)
                )
            )
            conn.commit()
    except Exception as e:
        logger.error(f"[OCR_TRIGGER_ERROR] Failed to create OCR result record: {e}")
    
    # Create job in queue
    job_id = None
    try:
        with engine.connect() as conn:
            job_service = JobQueueService(conn)
            job = job_service.create_job(
                hospital_id=hospital_id,
                job_type=JobType.OCR,
                payload={'document_id': document_id, 'file_path': file_path},
                document_id=document_id,
                created_by=created_by
            )
            job_id = job.id
    except Exception as e:
        logger.error(f"[JOB_QUEUE_ERROR] Failed to create job: {e}")
    
    # Trigger async task with job_id
    task = process_document_ocr_task.delay(document_id, hospital_id, file_path, job_id)
    
    logger.info(f"[OCR_TRIGGER_SUCCESS] Task ID: {task.id}, Job ID: {job_id}, Document ID: {document_id}")
    
    return job_id or task.id
