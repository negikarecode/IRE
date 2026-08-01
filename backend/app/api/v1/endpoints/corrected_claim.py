import logging
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import decode_token
from app.infrastructure.services.corrected_claim_service import get_corrected_claim_service
from app.infrastructure.db.models.claim import ClaimChangeStatus

logger = logging.getLogger("corrected_claim_api")
router = APIRouter()


class CorrectedClaimRequest(BaseModel):
    claim_id: str
    original_claim_data: dict
    validation_findings: Optional[List[dict]] = None
    coding_findings: Optional[List[dict]] = None
    leakage_findings: Optional[List[dict]] = None


class ChangeAcceptRequest(BaseModel):
    change_id: str


class ChangeRejectRequest(BaseModel):
    change_id: str


class ChangeEditRequest(BaseModel):
    change_id: str
    edited_value: str


class PreviewApproveRequest(BaseModel):
    preview_id: str


class CorrectedClaimResponse(BaseModel):
    preview_id: str
    claim_id: str
    hospital_id: str
    original_claim: dict
    corrected_claim: dict
    changes: List[dict]
    total_changes: int
    status: str


class ChangeResponse(BaseModel):
    id: str
    field_name: str
    original_value: Optional[str]
    corrected_value: str
    change_type: str
    source: str
    source_finding_id: Optional[str]
    ai_recommendation: dict
    status: str
    created_at: str


from app.core.exceptions import UnauthorizedException, NotFoundException, BadRequestException

@router.post("/generate", status_code=status.HTTP_201_CREATED)
async def generate_corrected_claim(
    request: CorrectedClaimRequest,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Generate a corrected claim preview based on AI recommendations.
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
    
    corrected_claim_service = get_corrected_claim_service(db)
    
    result = corrected_claim_service.generate_corrected_claim(
        claim_id=request.claim_id,
        hospital_id=hospital_id,
        original_claim_data=request.original_claim_data,
        validation_findings=request.validation_findings,
        coding_findings=request.coding_findings,
        leakage_findings=request.leakage_findings
    )
    
    logger.info(f"[CORRECTED_CLAIM_API] Claim ID: {request.claim_id}, Changes: {result['total_changes']}")
    
    res = CorrectedClaimResponse(
        preview_id=result["preview_id"],
        claim_id=result["claim_id"],
        hospital_id=result["hospital_id"],
        original_claim=result["original_claim"],
        corrected_claim=result["corrected_claim"],
        changes=result["changes"],
        total_changes=result["total_changes"],
        status=result["status"]
    )
    return {
        "success": True,
        "message": "Corrected claim generated successfully",
        "data": res.model_dump()
    }


@router.get("/claims/{claim_id}/preview", status_code=status.HTTP_200_OK)
async def get_claim_preview(
    claim_id: str,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Get corrected claim preview for a claim.
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
    
    corrected_claim_service = get_corrected_claim_service(db)
    
    preview = corrected_claim_service.get_preview(claim_id, hospital_id)
    
    if not preview:
        raise NotFoundException(message="Corrected claim preview not found")
    
    changes = corrected_claim_service.get_changes(preview.id, hospital_id)
    
    data = {
        "preview_id": preview.id,
        "claim_id": preview.claim_id,
        "hospital_id": preview.hospital_id,
        "original_claim": preview.original_claim_data,
        "corrected_claim": preview.corrected_claim_data,
        "ai_recommendations": preview.ai_recommendations,
        "changes": [
            ChangeResponse(
                id=c.id,
                field_name=c.field_name,
                original_value=c.original_value,
                corrected_value=c.corrected_value,
                change_type=c.change_type,
                source=c.source,
                source_finding_id=c.source_finding_id,
                ai_recommendation=c.ai_recommendation or {},
                status=c.status,
                created_at=c.created_at.isoformat() if c.created_at else None
            ).model_dump()
            for c in changes
        ],
        "total_changes": preview.total_changes,
        "accepted_changes": preview.accepted_changes,
        "rejected_changes": preview.rejected_changes,
        "status": preview.status
    }
    return {
        "success": True,
        "message": "Claim preview retrieved successfully",
        "data": data
    }


@router.get("/previews/{preview_id}/changes", status_code=status.HTTP_200_OK)
async def get_preview_changes(
    preview_id: str,
    status: Optional[str] = None,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Get changes for a corrected claim preview.
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
    
    corrected_claim_service = get_corrected_claim_service(db)
    
    changes = corrected_claim_service.get_changes(preview_id, hospital_id, status)
    
    data = [
        ChangeResponse(
            id=c.id,
            field_name=c.field_name,
            original_value=c.original_value,
            corrected_value=c.edited_value if c.status == ClaimChangeStatus.EDITED.value else c.corrected_value,
            change_type=c.change_type,
            source=c.source,
            source_finding_id=c.source_finding_id,
            ai_recommendation=c.ai_recommendation or {},
            status=c.status,
            created_at=c.created_at.isoformat() if c.created_at else None
        ).model_dump()
        for c in changes
    ]
    return {
        "success": True,
        "message": "Preview changes retrieved successfully",
        "data": data
    }


@router.post("/changes/accept", status_code=status.HTTP_200_OK)
async def accept_change(
    request: ChangeAcceptRequest,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Accept a proposed change.
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
        raise UnauthorizedException(message="Token missing required user information")
    
    corrected_claim_service = get_corrected_claim_service(db)
    
    change = corrected_claim_service.accept_change(
        change_id=request.change_id,
        user_id=user_id,
        hospital_id=hospital_id
    )
    
    if not change:
        raise NotFoundException(message="Change not found")
    
    return {
        "success": True,
        "message": "Change accepted",
        "data": {"change_id": change.id}
    }


@router.post("/changes/reject", status_code=status.HTTP_200_OK)
async def reject_change(
    request: ChangeRejectRequest,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Reject a proposed change.
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
        raise UnauthorizedException(message="Token missing required user information")
    
    corrected_claim_service = get_corrected_claim_service(db)
    
    change = corrected_claim_service.reject_change(
        change_id=request.change_id,
        user_id=user_id,
        hospital_id=hospital_id
    )
    
    if not change:
        raise NotFoundException(message="Change not found")
    
    return {
        "success": True,
        "message": "Change rejected",
        "data": {"change_id": change.id}
    }


@router.post("/changes/edit", status_code=status.HTTP_200_OK)
async def edit_change(
    request: ChangeEditRequest,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Edit a proposed change with user's value.
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
        raise UnauthorizedException(message="Token missing required user information")
    
    corrected_claim_service = get_corrected_claim_service(db)
    
    change = corrected_claim_service.edit_change(
        change_id=request.change_id,
        edited_value=request.edited_value,
        user_id=user_id,
        hospital_id=hospital_id
    )
    
    if not change:
        raise NotFoundException(message="Change not found")
    
    return {
        "success": True,
        "message": "Change edited",
        "data": {
            "change_id": change.id,
            "edited_value": change.edited_value
        }
    }


@router.post("/previews/approve", status_code=status.HTTP_200_OK)
async def approve_preview(
    request: PreviewApproveRequest,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Approve the corrected claim preview.
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
        raise UnauthorizedException(message="Token missing required user information")
    
    corrected_claim_service = get_corrected_claim_service(db)
    
    preview = corrected_claim_service.approve_preview(
        preview_id=request.preview_id,
        user_id=user_id,
        hospital_id=hospital_id
    )
    
    if not preview:
        raise NotFoundException(message="Preview not found")
    
    return {
        "success": True,
        "message": "Preview approved",
        "data": {
            "preview_id": preview.id,
            "claim_id": preview.claim_id,
            "accepted_changes": preview.accepted_changes
        }
    }
