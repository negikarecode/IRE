import os
import uuid
import logging
import hashlib
import aiofiles
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status, Header
from fastapi.responses import StreamingResponse, FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.config import settings
from app.infrastructure.db.models.claim import DocumentModel, ProcessingStatus, OCRResultModel, ClinicalExtractionModel, VirusScanStatus, RetentionPolicy
from app.core.security import decode_token
from app.infrastructure.tasks.ocr_tasks import trigger_ocr_processing
from app.infrastructure.storage.storage_backend import StorageService, get_storage_backend
from app.infrastructure.services.virus_scan_service import get_virus_scan_service

logger = logging.getLogger("document_upload")
router = APIRouter()

# Supported file formats and max size
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/tiff",
    "image/tif"
}

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


class DocumentUploadResponse(BaseModel):
    id: str
    hospital_id: str
    uploaded_by: str
    original_filename: str
    internal_filename: str
    mime_type: str
    file_size_bytes: int
    storage_location: str
    checksum: str
    processing_status: str
    upload_timestamp: str
    pages: Optional[int] = None
    document_type: Optional[str] = None
    job_id: Optional[str] = None
    virus_scan_status: Optional[str] = None
    retention_policy: Optional[str] = None


class ClinicalExtractionResponse(BaseModel):
    id: str
    document_id: str
    hospital_id: str
    patient_name: Optional[str]
    uhid: Optional[str]
    mrn: Optional[str]
    age: Optional[str]
    gender: Optional[str]
    admission_date: Optional[str]
    discharge_date: Optional[str]
    operation_date: Optional[str]
    length_of_stay: Optional[int]
    hospital: Optional[str]
    doctor: Optional[str]
    department: Optional[str]
    diagnosis: Optional[str]
    icd_codes: Optional[list]
    procedure: Optional[str]
    cpt_codes: Optional[list]
    medicines: Optional[list]
    implants: Optional[list]
    insurance_company: Optional[str]
    policy_number: Optional[str]
    bill_amount: Optional[float]
    invoice_number: Optional[str]
    extraction_confidence: Optional[float]
    extraction_timestamp: Optional[str]
    created_at: str


class UpdateClassificationRequest(BaseModel):
    document_type: str
    confidence: Optional[float] = None


class OCRResultResponse(BaseModel):
    id: str
    document_id: str
    hospital_id: str
    raw_text: Optional[str]
    structured_data: Optional[dict]
    ocr_confidence: Optional[float]
    processing_time_seconds: Optional[float]
    page_count: Optional[int]
    detected_language: Optional[str]
    processing_status: str
    error_message: Optional[str]
    started_at: Optional[str]
    completed_at: Optional[str]
    created_at: str


ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".tiff", ".tif"}

def validate_file(file: UploadFile) -> tuple[bool, Optional[str]]:
    """Validate file format, extension, and MIME type."""
    filename = file.filename or ""
    ext = os.path.splitext(filename)[1].lower()
    
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"Disallowed file extension '{ext}'. Allowed extensions: PDF, JPG, JPEG, PNG, TIFF"
    
    if file.content_type not in ALLOWED_MIME_TYPES:
        return False, f"Unsupported MIME type: {file.content_type}. Allowed: PDF, JPG, PNG, TIFF"
    
    return True, None


from app.core.exceptions import UnauthorizedException, NotFoundException, BadRequestException, ValidationException

@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    claim_id: Optional[str] = Form(None),
    retention_policy: Optional[str] = Form(None),
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload medical document with validation, secure storage, and checksum verification.
    """
    logger.info(f"[DOCUMENT_UPLOAD_START] Filename: '{file.filename}', MIME: '{file.content_type}'")
    
    if not authorization or not authorization.startswith("Bearer "):
        raise UnauthorizedException(message="Missing or invalid authorization token")
    
    token = authorization.split(" ")[1]
    payload = decode_token(token)
    
    if not payload:
        raise UnauthorizedException(message="Invalid or expired token")
    
    user_id = payload.get("sub")
    hospital_id = payload.get("hospital_id")
    
    if not user_id or not hospital_id:
        raise UnauthorizedException(message="Token missing required user or hospital information")
    
    is_valid, error_msg = validate_file(file)
    if not is_valid:
        raise ValidationException(message=error_msg)
    
    sha256 = hashlib.sha256()
    chunks = []
    file_size = 0
    CHUNK_SIZE = 64 * 1024  # 64 KB streaming buffer
    
    while True:
        chunk = await file.read(CHUNK_SIZE)
        if not chunk:
            break
        file_size += len(chunk)
        if file_size > MAX_FILE_SIZE:
            raise ValidationException(message="File size exceeds maximum limit of 50 MB")
        sha256.update(chunk)
        chunks.append(chunk)
        
    content = b"".join(chunks)
    checksum = sha256.hexdigest()
    
    storage_backend = get_storage_backend()
    storage_service = StorageService(storage_backend)
    
    storage_metadata = await storage_service.upload_document(
        file_content=content,
        original_filename=file.filename,
        hospital_id=hospital_id,
        user_id=user_id
    )
    
    policy = retention_policy or RetentionPolicy.PERMANENT.value
    if policy not in [e.value for e in RetentionPolicy]:
        policy = RetentionPolicy.PERMANENT.value
    
    retention_until = None
    if policy != RetentionPolicy.PERMANENT.value:
        if policy == RetentionPolicy.DAYS_30.value:
            retention_until = datetime.now(timezone.utc) + timedelta(days=30)
        elif policy == RetentionPolicy.DAYS_90.value:
            retention_until = datetime.now(timezone.utc) + timedelta(days=90)
        elif policy == RetentionPolicy.DAYS_180.value:
            retention_until = datetime.now(timezone.utc) + timedelta(days=180)
        elif policy == RetentionPolicy.DAYS_365.value:
            retention_until = datetime.now(timezone.utc) + timedelta(days=365)
    
    document = DocumentModel(
        id=str(uuid.uuid4()),
        hospital_id=hospital_id,
        uploaded_by=user_id,
        claim_id=claim_id,
        original_filename=file.filename,
        internal_filename=storage_metadata["internal_filename"],
        mime_type=file.content_type or "application/octet-stream",
        file_size_bytes=file_size,
        storage_location=storage_metadata["storage_path"],
        checksum=storage_metadata["checksum"],
        processing_status=ProcessingStatus.PENDING.value,
        virus_scan_status=VirusScanStatus.PENDING.value,
        retention_policy=policy,
        retention_until=retention_until
    )
    db.add(document)
    await db.commit()
    await db.refresh(document)
    
    logger.info(f"[DOCUMENT_UPLOAD_SUCCESS] Document ID: {document.id}, Internal Filename: {document.internal_filename}")
    
    virus_scan_service = get_virus_scan_service()
    try:
        document.virus_scan_status = VirusScanStatus.SCANNING.value
        document.virus_scan_timestamp = datetime.now(timezone.utc)
        await db.commit()
        
        scan_result = await virus_scan_service.scan_file_content(content, file.filename)
        
        document.virus_scan_status = scan_result['status']
        document.virus_scan_timestamp = datetime.now(timezone.utc)
        document.virus_scan_engine = scan_result['engine']
        
        if scan_result['status'] == 'infected':
            document.marked_for_deletion = 1
        
        await db.commit()
    except Exception as scan_error:
        document.virus_scan_status = VirusScanStatus.ERROR.value
        await db.commit()
    
    job_id = None
    if document.virus_scan_status in [VirusScanStatus.CLEAN.value, VirusScanStatus.SKIPPED.value]:
        try:
            job_id = trigger_ocr_processing(document.id, hospital_id, storage_metadata["storage_path"], user_id)
        except Exception:
            pass
    
    res = DocumentUploadResponse(
        id=document.id,
        hospital_id=document.hospital_id,
        uploaded_by=document.uploaded_by,
        original_filename=document.original_filename,
        internal_filename=document.internal_filename,
        mime_type=document.mime_type,
        file_size_bytes=document.file_size_bytes,
        storage_location=document.storage_location,
        checksum=document.checksum,
        processing_status=document.processing_status,
        upload_timestamp=document.upload_timestamp.isoformat(),
        pages=document.pages,
        document_type=document.document_type,
        job_id=job_id,
        virus_scan_status=document.virus_scan_status,
        retention_policy=document.retention_policy
    )
    return {
        "success": True,
        "message": "Document uploaded successfully",
        "data": res.model_dump()
    }


@router.get("/", status_code=status.HTTP_200_OK)
async def list_documents(
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """List all documents for the authenticated user's hospital."""
    if not authorization or not authorization.startswith("Bearer "):
        raise UnauthorizedException(message="Missing or invalid authorization token")
    
    token = authorization.split(" ")[1]
    payload = decode_token(token)
    
    if not payload:
        raise UnauthorizedException(message="Invalid or expired token")
    
    hospital_id = payload.get("hospital_id")
    
    if not hospital_id:
        raise UnauthorizedException(message="Token missing hospital information")
    
    result = await db.execute(
        select(DocumentModel).where(DocumentModel.hospital_id == hospital_id)
    )
    documents = result.scalars().all()
    
    data = [
        DocumentUploadResponse(
            id=doc.id,
            hospital_id=doc.hospital_id,
            uploaded_by=doc.uploaded_by,
            original_filename=doc.original_filename,
            mime_type=doc.mime_type,
            file_size_bytes=doc.file_size_bytes,
            storage_location=doc.storage_location,
            checksum=doc.checksum or "",
            internal_filename=doc.internal_filename or "",
            processing_status=doc.processing_status,
            upload_timestamp=doc.upload_timestamp.isoformat(),
            pages=doc.pages,
            document_type=doc.document_type
        ).model_dump()
        for doc in documents
    ]
    return {
        "success": True,
        "message": "Documents retrieved successfully",
        "data": data
    }


@router.get("/{document_id}", status_code=status.HTTP_200_OK)
async def get_document(
    document_id: str,
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific document by ID."""
    if not authorization or not authorization.startswith("Bearer "):
        raise UnauthorizedException(message="Missing or invalid authorization token")
    
    token = authorization.split(" ")[1]
    payload = decode_token(token)
    
    if not payload:
        raise UnauthorizedException(message="Invalid or expired token")
    
    hospital_id = payload.get("hospital_id")
    
    if not hospital_id:
        raise UnauthorizedException(message="Token missing hospital information")
    
    result = await db.execute(
        select(DocumentModel).where(
            DocumentModel.id == document_id,
            DocumentModel.hospital_id == hospital_id
        )
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise NotFoundException(message="Document not found")
    
    res = DocumentUploadResponse(
        id=document.id,
        hospital_id=document.hospital_id,
        uploaded_by=document.uploaded_by,
        original_filename=document.original_filename,
        checksum=document.checksum or "",
        internal_filename=document.internal_filename or "",
        mime_type=document.mime_type,
        file_size_bytes=document.file_size_bytes,
        storage_location=document.storage_location,
        processing_status=document.processing_status,
        upload_timestamp=document.upload_timestamp.isoformat(),
        pages=document.pages,
        document_type=document.document_type
    )
    return {
        "success": True,
        "message": "Document retrieved successfully",
        "data": res.model_dump()
    }


@router.get("/{document_id}/clinical", status_code=status.HTTP_200_OK)
async def get_clinical_extraction(
    document_id: str,
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """Get clinical extraction data for a specific document."""
    if not authorization or not authorization.startswith("Bearer "):
        raise UnauthorizedException(message="Missing or invalid authorization token")
    
    token = authorization.split(" ")[1]
    payload = decode_token(token)
    
    if not payload:
        raise UnauthorizedException(message="Invalid or expired token")
    
    hospital_id = payload.get("hospital_id")
    
    if not hospital_id:
        raise UnauthorizedException(message="Token missing hospital information")
    
    result = await db.execute(
        select(ClinicalExtractionModel).where(
            ClinicalExtractionModel.document_id == document_id,
            ClinicalExtractionModel.hospital_id == hospital_id
        )
    )
    extraction = result.scalar_one_or_none()
    
    if not extraction:
        raise NotFoundException(message="Clinical extraction not found")
    
    res = ClinicalExtractionResponse(
        id=extraction.id,
        document_id=extraction.document_id,
        hospital_id=extraction.hospital_id,
        patient_name=extraction.patient_name,
        uhid=extraction.uhid,
        mrn=extraction.mrn,
        age=extraction.age,
        gender=extraction.gender,
        admission_date=extraction.admission_date,
        discharge_date=extraction.discharge_date,
        operation_date=extraction.operation_date,
        length_of_stay=extraction.length_of_stay,
        hospital=extraction.hospital,
        doctor=extraction.doctor,
        department=extraction.department,
        diagnosis=extraction.diagnosis,
        icd_codes=extraction.icd_codes,
        procedure=extraction.procedure,
        cpt_codes=extraction.cpt_codes,
        medicines=extraction.medicines,
        implants=extraction.implants,
        insurance_company=extraction.insurance_company,
        policy_number=extraction.policy_number,
        bill_amount=extraction.bill_amount,
        invoice_number=extraction.invoice_number,
        extraction_confidence=extraction.extraction_confidence,
        extraction_timestamp=extraction.extraction_timestamp.isoformat() if extraction.extraction_timestamp else None,
        created_at=extraction.created_at.isoformat()
    )
    return {
        "success": True,
        "message": "Clinical extraction retrieved successfully",
        "data": res.model_dump()
    }


@router.put("/{document_id}/classification", status_code=status.HTTP_200_OK)
async def update_document_classification(
    document_id: str,
    classification: UpdateClassificationRequest,
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """Manually update document classification."""
    if not authorization or not authorization.startswith("Bearer "):
        raise UnauthorizedException(message="Missing or invalid authorization token")
    
    token = authorization.split(" ")[1]
    payload = decode_token(token)
    
    if not payload:
        raise UnauthorizedException(message="Invalid or expired token")
    
    hospital_id = payload.get("hospital_id")
    
    if not hospital_id:
        raise UnauthorizedException(message="Token missing hospital information")
    
    valid_types = [
        "discharge_summary", "operative_note", "final_bill", "prescription",
        "authorization_letter", "investigation_report", "lab_report",
        "radiology_report", "insurance_form", "consent_form", "unknown"
    ]
    
    if classification.document_type not in valid_types:
        raise ValidationException(message=f"Invalid document type. Must be one of: {', '.join(valid_types)}")
    
    result = await db.execute(
        select(DocumentModel).where(
            DocumentModel.id == document_id,
            DocumentModel.hospital_id == hospital_id
        )
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise NotFoundException(message="Document not found")
    
    document.document_type = classification.document_type
    document.classification_confidence = classification.confidence if classification.confidence is not None else 1.0
    document.is_manually_classified = 1
    
    await db.commit()
    await db.refresh(document)
    
    res = DocumentUploadResponse(
        id=document.id,
        hospital_id=document.hospital_id,
        uploaded_by=document.uploaded_by,
        original_filename=document.original_filename,
        checksum=document.checksum or "",
        internal_filename=document.internal_filename or "",
        mime_type=document.mime_type,
        file_size_bytes=document.file_size_bytes,
        storage_location=document.storage_location,
        processing_status=document.processing_status,
        upload_timestamp=document.upload_timestamp.isoformat(),
        pages=document.pages,
        document_type=document.document_type
    )
    return {
        "success": True,
        "message": "Document classification updated successfully",
        "data": res.model_dump()
    }


@router.get("/{document_id}/ocr", status_code=status.HTTP_200_OK)
async def get_ocr_result(
    document_id: str,
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """Get OCR result for a specific document."""
    if not authorization or not authorization.startswith("Bearer "):
        raise UnauthorizedException(message="Missing or invalid authorization token")
    
    token = authorization.split(" ")[1]
    payload = decode_token(token)
    
    if not payload:
        raise UnauthorizedException(message="Invalid or expired token")
    
    hospital_id = payload.get("hospital_id")
    
    if not hospital_id:
        raise UnauthorizedException(message="Token missing hospital information")
    
    result = await db.execute(
        select(OCRResultModel).where(
            OCRResultModel.document_id == document_id,
            OCRResultModel.hospital_id == hospital_id
        )
    )
    ocr_result = result.scalar_one_or_none()
    
    if not ocr_result:
        raise NotFoundException(message="OCR result not found")
    
    res = OCRResultResponse(
        id=ocr_result.id,
        document_id=ocr_result.document_id,
        hospital_id=ocr_result.hospital_id,
        raw_text=ocr_result.raw_text,
        structured_data=ocr_result.structured_data,
        ocr_confidence=ocr_result.ocr_confidence,
        processing_time_seconds=ocr_result.processing_time_seconds,
        page_count=ocr_result.page_count,
        detected_language=ocr_result.detected_language,
        processing_status=ocr_result.processing_status,
        error_message=ocr_result.error_message,
        started_at=ocr_result.started_at.isoformat() if ocr_result.started_at else None,
        completed_at=ocr_result.completed_at.isoformat() if ocr_result.completed_at else None,
        created_at=ocr_result.created_at.isoformat()
    )
    return {
        "success": True,
        "message": "OCR result retrieved successfully",
        "data": res.model_dump()
    }


@router.delete("/{document_id}", status_code=status.HTTP_200_OK)
async def delete_document(
    document_id: str,
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """Delete a document by ID."""
    if not authorization or not authorization.startswith("Bearer "):
        raise UnauthorizedException(message="Missing or invalid authorization token")
    
    token = authorization.split(" ")[1]
    payload = decode_token(token)
    
    if not payload:
        raise UnauthorizedException(message="Invalid or expired token")
    
    hospital_id = payload.get("hospital_id")
    
    if not hospital_id:
        raise UnauthorizedException(message="Token missing hospital information")
    
    result = await db.execute(
        select(DocumentModel).where(
            DocumentModel.id == document_id,
            DocumentModel.hospital_id == hospital_id
        )
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise NotFoundException(message="Document not found")
    
    try:
        if os.path.exists(document.storage_location):
            os.remove(document.storage_location)
    except Exception as e:
        logger.warning(f"[DOCUMENT_DELETE_WARNING] Failed to delete file: {e}")
    
    await db.delete(document)
    await db.commit()
    
    return {"success": True, "message": "Document deleted successfully", "data": {}}


@router.get("/download/{document_id}")
async def download_document(
    document_id: str,
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Download a document securely with hospital access control.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise UnauthorizedException(message="Missing or invalid authorization token")
    
    token = authorization.split(" ")[1]
    payload = decode_token(token)
    
    if not payload:
        raise UnauthorizedException(message="Invalid or expired token")
    
    user_id = payload.get("sub")
    hospital_id = payload.get("hospital_id")
    
    if not user_id or not hospital_id:
        raise UnauthorizedException(message="Token missing required user or hospital information")
    
    result = await db.execute(
        select(DocumentModel).where(DocumentModel.id == document_id)
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise NotFoundException(message="Document not found")
    
    if document.hospital_id != hospital_id:
        raise BadRequestException(message="You do not have permission to access this document")
    
    if document.marked_for_deletion == 1:
        raise NotFoundException(message="Document has been deleted")
    
    if document.virus_scan_status == VirusScanStatus.INFECTED.value:
        raise BadRequestException(message="Document failed virus scan and cannot be downloaded")
    
    try:
        storage_backend = get_storage_backend()
        storage_service = StorageService(storage_backend)
        
        file_content = await storage_service.download_document(
            internal_filename=document.internal_filename,
            hospital_id=hospital_id
        )
        
        document.access_count = (document.access_count or 0) + 1
        document.last_accessed_at = datetime.now(timezone.utc)
        document.last_accessed_by = user_id
        await db.commit()
        
        return StreamingResponse(
            iter([file_content]),
            media_type=document.mime_type,
            headers={
                "Content-Disposition": f"attachment; filename=\"{document.original_filename}\"",
                "Content-Length": str(len(file_content)),
                "X-Checksum": document.checksum,
                "X-Document-ID": document.id
            }
        )
        
    except FileNotFoundError:
        raise NotFoundException(message="File not found in storage")
    except Exception as e:
        raise BadRequestException(message=f"Failed to download document: {str(e)}")


@router.put("/{document_id}/retention", status_code=status.HTTP_200_OK)
async def update_document_retention(
    document_id: str,
    policy: str = Form(...),
    custom_retention_days: Optional[int] = Form(None),
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Update retention policy for a document.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise UnauthorizedException(message="Missing or invalid authorization token")
    
    token = authorization.split(" ")[1]
    payload = decode_token(token)
    
    if not payload:
        raise UnauthorizedException(message="Invalid or expired token")
    
    hospital_id = payload.get("hospital_id")
    
    if not hospital_id:
        raise UnauthorizedException(message="Token missing hospital information")
    
    try:
        retention_policy = RetentionPolicy(policy)
    except ValueError:
        raise BadRequestException(message=f"Invalid retention policy: {policy}")
    
    result = await db.execute(
        select(DocumentModel).where(
            DocumentModel.id == document_id,
            DocumentModel.hospital_id == hospital_id
        )
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise NotFoundException(message="Document not found")
    
    document.retention_policy = retention_policy.value
    
    if retention_policy == RetentionPolicy.PERMANENT:
        document.retention_until = None
    elif retention_policy == RetentionPolicy.DAYS_30:
        document.retention_until = datetime.now(timezone.utc) + timedelta(days=30)
    elif retention_policy == RetentionPolicy.DAYS_90:
        document.retention_until = datetime.now(timezone.utc) + timedelta(days=90)
    elif retention_policy == RetentionPolicy.DAYS_180:
        document.retention_until = datetime.now(timezone.utc) + timedelta(days=180)
    elif retention_policy == RetentionPolicy.DAYS_365:
        document.retention_until = datetime.now(timezone.utc) + timedelta(days=365)
    elif retention_policy == RetentionPolicy.CUSTOM and custom_retention_days:
        document.retention_until = datetime.now(timezone.utc) + timedelta(days=custom_retention_days)
    
    await db.commit()
    await db.refresh(document)
    
    return {
        "success": True,
        "message": "Retention policy updated",
        "data": {
            "document_id": document.id,
            "retention_policy": document.retention_policy,
            "retention_until": document.retention_until.isoformat() if document.retention_until else None
        }
    }


@router.get("/retention/statistics", status_code=status.HTTP_200_OK)
async def get_retention_statistics(
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Get retention statistics for the hospital's documents.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise UnauthorizedException(message="Missing or invalid authorization token")
    
    token = authorization.split(" ")[1]
    payload = decode_token(token)
    
    if not payload:
        raise UnauthorizedException(message="Invalid or expired token")
    
    hospital_id = payload.get("hospital_id")
    
    if not hospital_id:
        raise UnauthorizedException(message="Token missing hospital information")
    
    result = await db.execute(
        select(DocumentModel).where(DocumentModel.hospital_id == hospital_id)
    )
    documents = result.scalars().all()
    
    stats = {
        "total_documents": len(documents),
        "by_policy": {},
        "marked_for_deletion": 0,
        "expired_not_marked": 0
    }
    
    now = datetime.now(timezone.utc)
    
    for doc in documents:
        policy = doc.retention_policy or "unknown"
        stats["by_policy"][policy] = stats["by_policy"].get(policy, 0) + 1
        
        if doc.marked_for_deletion == 1:
            stats["marked_for_deletion"] += 1
        
        if doc.retention_until and doc.retention_until < now and doc.marked_for_deletion == 0:
            stats["expired_not_marked"] += 1
    
    return {
        "success": True,
        "message": "Retention statistics retrieved successfully",
        "data": stats
    }
