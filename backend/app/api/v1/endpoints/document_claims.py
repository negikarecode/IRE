import logging
from fastapi import APIRouter, Depends, status, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import decode_token
from app.infrastructure.db.models.claim import DocumentClaimModel, DocumentModel
from app.infrastructure.services.claim_assembly_service import claim_assembly_service

logger = logging.getLogger("document_claims")
router = APIRouter()


class DocumentClaimCreate(BaseModel):
    document_ids: Optional[List[str]] = None


class DocumentClaimResponse(BaseModel):
    id: str
    hospital_id: str
    claim_number: str
    status: str
    required_document_types: Optional[List[str]]
    missing_document_types: Optional[List[str]]
    created_by: str
    created_at: str
    updated_at: str


class DocumentClaimSummary(BaseModel):
    claim_id: str
    claim_number: str
    status: str
    total_documents: int
    document_type_counts: dict
    required_document_types: Optional[List[str]]
    missing_document_types: Optional[List[str]]
    is_complete: bool
    created_at: str
    updated_at: str


from app.core.exceptions import UnauthorizedException, NotFoundException

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_document_claim(
    claim_data: DocumentClaimCreate,
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """Create a new document claim."""
    if not authorization or not authorization.startswith("Bearer "):
        raise UnauthorizedException(message="Missing or invalid authorization token")
    
    token = authorization.split(" ")[1]
    payload = decode_token(token)
    
    if not payload:
        raise UnauthorizedException(message="Invalid or expired token")
    
    hospital_id = payload.get("hospital_id")
    user_id = payload.get("sub")
    
    if not hospital_id or not user_id:
        raise UnauthorizedException(message="Token missing required information")
    
    claim = await claim_assembly_service.create_claim(
        hospital_id=hospital_id,
        created_by=user_id,
        document_ids=claim_data.document_ids,
        db=db
    )
    
    res = DocumentClaimResponse(
        id=claim.id,
        hospital_id=claim.hospital_id,
        claim_number=claim.claim_number,
        status=claim.status,
        required_document_types=claim.required_document_types,
        missing_document_types=claim.missing_document_types,
        created_by=claim.created_by,
        created_at=claim.created_at.isoformat(),
        updated_at=claim.updated_at.isoformat()
    )
    return {
        "success": True,
        "message": "Document claim created successfully",
        "data": res.model_dump()
    }


@router.get("/", status_code=status.HTTP_200_OK)
async def list_document_claims(
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """List all document claims for the hospital."""
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
        select(DocumentClaimModel).where(DocumentClaimModel.hospital_id == hospital_id)
    )
    claims = result.scalars().all()
    
    data = [
        DocumentClaimResponse(
            id=claim.id,
            hospital_id=claim.hospital_id,
            claim_number=claim.claim_number,
            status=claim.status,
            required_document_types=claim.required_document_types,
            missing_document_types=claim.missing_document_types,
            created_by=claim.created_by,
            created_at=claim.created_at.isoformat(),
            updated_at=claim.updated_at.isoformat()
        ).model_dump()
        for claim in claims
    ]
    return {
        "success": True,
        "message": "Document claims retrieved successfully",
        "data": data
    }


@router.get("/{claim_id}", status_code=status.HTTP_200_OK)
async def get_document_claim(
    claim_id: str,
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """Get detailed information about a specific claim."""
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
        select(DocumentClaimModel).where(
            DocumentClaimModel.id == claim_id,
            DocumentClaimModel.hospital_id == hospital_id
        )
    )
    claim = result.scalar_one_or_none()
    
    if not claim:
        raise NotFoundException(message="Claim not found")
    
    summary = await claim_assembly_service.get_claim_summary(claim_id, db)
    
    res = DocumentClaimSummary(**summary)
    return {
        "success": True,
        "message": "Document claim details retrieved successfully",
        "data": res.model_dump()
    }


@router.post("/{claim_id}/documents", status_code=status.HTTP_200_OK)
async def link_documents_to_claim(
    claim_id: str,
    document_ids: List[str],
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """Link documents to a claim."""
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
        select(DocumentClaimModel).where(
            DocumentClaimModel.id == claim_id,
            DocumentClaimModel.hospital_id == hospital_id
        )
    )
    claim = result.scalar_one_or_none()
    
    if not claim:
        raise NotFoundException(message="Claim not found")
    
    await claim_assembly_service.link_documents_to_claim(claim_id, document_ids, db)
    
    return {
        "success": True,
        "message": "Documents linked successfully",
        "data": {}
    }


@router.delete("/{claim_id}/documents/{document_id}", status_code=status.HTTP_200_OK)
async def unlink_document_from_claim(
    claim_id: str,
    document_id: str,
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """Unlink a document from a claim."""
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
        select(DocumentClaimModel).where(
            DocumentClaimModel.id == claim_id,
            DocumentClaimModel.hospital_id == hospital_id
        )
    )
    claim = result.scalar_one_or_none()
    
    if not claim:
        raise NotFoundException(message="Claim not found")
    
    await claim_assembly_service.unlink_document_from_claim(document_id, db)
    
    return {
        "success": True,
        "message": "Document unlinked successfully",
        "data": {}
    }


class ClaimDocumentResponse(BaseModel):
    id: str
    hospital_id: str
    uploaded_by: str
    claim_id: Optional[str]
    original_filename: str
    mime_type: str
    file_size_bytes: int
    storage_location: str
    processing_status: str
    pages: Optional[int]
    document_type: Optional[str]
    classification_confidence: Optional[float]
    is_manually_classified: Optional[int]
    upload_timestamp: str
    created_at: str


@router.get("/{claim_id}/documents", status_code=status.HTTP_200_OK)
async def get_claim_documents(
    claim_id: str,
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """Get all documents linked to a claim."""
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
        select(DocumentClaimModel).where(
            DocumentClaimModel.id == claim_id,
            DocumentClaimModel.hospital_id == hospital_id
        )
    )
    claim = result.scalar_one_or_none()
    
    if not claim:
        raise NotFoundException(message="Claim not found")
    
    documents = await claim_assembly_service.get_claim_documents(claim_id, db)
    
    data = [
        ClaimDocumentResponse(
            id=doc.id,
            hospital_id=doc.hospital_id,
            uploaded_by=doc.uploaded_by,
            claim_id=doc.claim_id,
            original_filename=doc.original_filename,
            mime_type=doc.mime_type,
            file_size_bytes=doc.file_size_bytes,
            storage_location=doc.storage_location,
            processing_status=doc.processing_status,
            pages=doc.pages,
            document_type=doc.document_type,
            classification_confidence=doc.classification_confidence,
            is_manually_classified=doc.is_manually_classified,
            upload_timestamp=doc.upload_timestamp.isoformat(),
            created_at=doc.created_at.isoformat()
        ).model_dump()
        for doc in documents
    ]
    return {
        "success": True,
        "message": "Claim documents retrieved successfully",
        "data": data
    }


@router.post("/auto-group", status_code=status.HTTP_200_OK)
async def auto_group_documents(
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """Automatically group unlinked documents into claims."""
    if not authorization or not authorization.startswith("Bearer "):
        raise UnauthorizedException(message="Missing or invalid authorization token")
    
    token = authorization.split(" ")[1]
    payload = decode_token(token)
    
    if not payload:
        raise UnauthorizedException(message="Invalid or expired token")
    
    hospital_id = payload.get("hospital_id")
    user_id = payload.get("sub")
    
    if not hospital_id or not user_id:
        raise UnauthorizedException(message="Token missing required information")
    
    claims = await claim_assembly_service.auto_group_documents(
        hospital_id=hospital_id,
        user_id=user_id,
        db=db
    )
    
    return {
        "success": True,
        "message": f"Created {len(claims)} claims",
        "data": {
            "claims_created": len(claims)
        }
    }
