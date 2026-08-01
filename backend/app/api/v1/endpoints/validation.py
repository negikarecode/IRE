import logging
from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import decode_token
from app.core.api_response import APIResponse
from app.core.exceptions import UnauthorizedException, NotFoundException, ValidationException as APIValidationException
from app.infrastructure.services.validation_service import get_validation_service
from app.infrastructure.db.models.claim import ValidationSeverity

logger = logging.getLogger("validation_api")
router = APIRouter()


class ValidationRequest(BaseModel):
    claim_id: str
    documents: List[dict]
    clinical_data_list: List[dict]
    claim_data: dict
    ocr_texts: Optional[dict] = None


class FindingAcknowledgeRequest(BaseModel):
    finding_id: str
    reason: Optional[str] = None


class FindingDismissRequest(BaseModel):
    finding_id: str
    reason: Optional[str] = None


class ValidationResponse(BaseModel):
    claim_id: str
    hospital_id: str
    total_findings: int
    findings: List[dict]
    summary: dict
    can_submit: bool


class FindingResponse(BaseModel):
    id: str
    claim_id: str
    severity: str
    category: str
    confidence: float
    affected_document: Optional[str]
    affected_field: Optional[str]
    explanation: str
    recommended_fix: Optional[str]
    status: str
    created_at: str


class SummaryResponse(BaseModel):
    claim_id: str
    total_findings: int
    critical_findings: int
    high_findings: int
    medium_findings: int
    low_findings: int
    overall_status: str
    overall_confidence: float
    validated_at: str


@router.post("/validate")
async def validate_claim(
    request: ValidationRequest,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Validate a claim before submission.
    
    Performs comprehensive validation including:
    - Missing mandatory documents
    - Missing diagnosis
    - Missing signatures/authorization
    - Coding inconsistencies
    - Patient mismatches
    - Date inconsistencies
    - Duplicate billing
    - Document completeness
    - Missing credentials/identifiers
    """
    # Validate authentication
    if not authorization or not authorization.startswith("Bearer "):
        raise UnauthorizedException("Missing or invalid authorization token")
    
    # Extract user info from JWT token
    token = authorization.split(" ")[1]
    payload = decode_token(token)
    
    if not payload:
        raise UnauthorizedException("Invalid or expired token")
    
    hospital_id = payload.get("hospital_id")
    
    if not hospital_id:
        raise UnauthorizedException("Token missing hospital information")
    
    try:
        validation_service = get_validation_service(db)
        
        result = validation_service.validate_claim(
            claim_id=request.claim_id,
            hospital_id=hospital_id,
            documents=request.documents,
            clinical_data_list=request.clinical_data_list,
            claim_data=request.claim_data,
            ocr_texts=request.ocr_texts
        )
        
        logger.info(f"[VALIDATION_API] Claim ID: {request.claim_id}, Findings: {result['total_findings']}")
        
        response_data, status_code = APIResponse.success(
            message="Claim validation completed successfully",
            data=result
        )
        
        return response_data
        
    except Exception as e:
        logger.error(f"[VALIDATION_API_ERROR] Claim ID: {request.claim_id}, Error: {str(e)}")
        raise APIValidationException(f"Failed to validate claim: {str(e)}")


@router.post("/revalidate")
async def revalidate_claim(
    request: ValidationRequest,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Re-validate a claim (clears old findings and creates new ones).
    """
    # Validate authentication
    if not authorization or not authorization.startswith("Bearer "):
        raise UnauthorizedException("Missing or invalid authorization token")
    
    # Extract user info from JWT token
    token = authorization.split(" ")[1]
    payload = decode_token(token)
    
    if not payload:
        raise UnauthorizedException("Invalid or expired token")
    
    hospital_id = payload.get("hospital_id")
    
    if not hospital_id:
        raise UnauthorizedException("Token missing hospital information")
    
    try:
        validation_service = get_validation_service(db)
        
        result = validation_service.revalidate_claim(
            claim_id=request.claim_id,
            hospital_id=hospital_id,
            documents=request.documents,
            clinical_data_list=request.clinical_data_list,
            claim_data=request.claim_data,
            ocr_texts=request.ocr_texts
        )
        
        logger.info(f"[CLAIM_REVALIDATION_API] Claim ID: {request.claim_id}, Findings: {result['total_findings']}")
        
        response_data, status_code = APIResponse.success(
            message="Claim re-validation completed successfully",
            data=result
        )
        
        return response_data
        
    except Exception as e:
        logger.error(f"[REVALIDATION_API_ERROR] Claim ID: {request.claim_id}, Error: {str(e)}")
        raise APIValidationException(f"Failed to re-validate claim: {str(e)}")


@router.get("/claims/{claim_id}/findings")
async def get_claim_findings(
    claim_id: str,
    severity: Optional[str] = None,
    status: Optional[str] = None,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Get validation findings for a claim.
    
    Query parameters:
    - severity: Filter by severity (critical, high, medium, low, info)
    - status: Filter by status (open, acknowledged, fixed, dismissed)
    """
    # Validate authentication
    if not authorization or not authorization.startswith("Bearer "):
        raise UnauthorizedException("Missing or invalid authorization token")
    
    # Extract hospital_id from JWT token
    token = authorization.split(" ")[1]
    payload = decode_token(token)
    
    if not payload:
        raise UnauthorizedException("Invalid or expired token")
    
    hospital_id = payload.get("hospital_id")
    
    if not hospital_id:
        raise UnauthorizedException("Token missing hospital information")
    
    try:
        validation_service = get_validation_service(db)
        
        findings = validation_service.get_findings_for_claim(
            claim_id=claim_id,
            hospital_id=hospital_id,
            severity=severity,
            status=status
        )
        
        response_data, status_code = APIResponse.success(
            message="Validation findings retrieved successfully",
            data=[{
                "id": f.id,
                "claim_id": f.claim_id,
                "severity": f.severity,
                "category": f.category,
                "confidence": f.confidence,
                "affected_document": f.affected_document,
                "affected_field": f.affected_field,
                "explanation": f.explanation,
                "recommended_fix": f.recommended_fix,
                "status": f.status,
                "created_at": f.created_at.isoformat() if f.created_at else None
            } for f in findings]
        )
        
        return response_data
        
    except Exception as e:
        logger.error(f"[GET_FINDINGS_ERROR] Claim ID: {claim_id}, Error: {str(e)}")
        raise APIValidationException(f"Failed to retrieve findings: {str(e)}")


@router.get("/claims/{claim_id}/summary")
async def get_claim_summary(
    claim_id: str,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Get validation summary for a claim.
    """
    # Validate authentication
    if not authorization or not authorization.startswith("Bearer "):
        raise UnauthorizedException("Missing or invalid authorization token")
    
    # Extract hospital_id from JWT token
    token = authorization.split(" ")[1]
    payload = decode_token(token)
    
    if not payload:
        raise UnauthorizedException("Invalid or expired token")
    
    hospital_id = payload.get("hospital_id")
    
    if not hospital_id:
        raise UnauthorizedException("Token missing hospital information")
    
    try:
        validation_service = get_validation_service(db)
        
        summary = validation_service.get_summary_for_claim(claim_id, hospital_id)
        
        if not summary:
            raise NotFoundException("Validation summary not found")
        
        response_data, status_code = APIResponse.success(
            message="Validation summary retrieved successfully",
            data={
                "claim_id": summary.claim_id,
                "total_findings": summary.total_findings,
                "critical_findings": summary.critical_findings,
                "high_findings": summary.high_findings,
                "medium_findings": summary.medium_findings,
                "low_findings": summary.low_findings,
                "overall_status": summary.overall_status,
                "overall_confidence": summary.overall_confidence or 0.0,
                "validated_at": summary.validated_at.isoformat() if summary.validated_at else None
            }
        )
        
        return response_data
        
    except NotFoundException:
        raise
    except Exception as e:
        logger.error(f"[GET_SUMMARY_ERROR] Claim ID: {claim_id}, Error: {str(e)}")
        raise APIValidationException(f"Failed to retrieve summary: {str(e)}")


@router.post("/findings/acknowledge")
async def acknowledge_finding(
    request: FindingAcknowledgeRequest,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Acknowledge a validation finding.
    """
    # Validate authentication
    if not authorization or not authorization.startswith("Bearer "):
        raise UnauthorizedException("Missing or invalid authorization token")
    
    # Extract user info from JWT token
    token = authorization.split(" ")[1]
    payload = decode_token(token)
    
    if not payload:
        raise UnauthorizedException("Invalid or expired token")
    
    user_id = payload.get("sub")
    hospital_id = payload.get("hospital_id")
    
    if not user_id or not hospital_id:
        raise UnauthorizedException("Token missing required user information")
    
    try:
        validation_service = get_validation_service(db)
        
        finding = validation_service.acknowledge_finding(
            finding_id=request.finding_id,
            user_id=user_id,
            hospital_id=hospital_id
        )
        
        if not finding:
            raise NotFoundException("Finding not found")
        
        response_data, status_code = APIResponse.success(
            message="Finding acknowledged successfully",
            data={"finding_id": finding.id}
        )
        
        return response_data
        
    except NotFoundException:
        raise
    except Exception as e:
        logger.error(f"[ACKNOWLEDGE_FINDING_ERROR] Finding ID: {request.finding_id}, Error: {str(e)}")
        raise APIValidationException(f"Failed to acknowledge finding: {str(e)}")


@router.post("/findings/fixed")
async def mark_finding_fixed(
    request: FindingAcknowledgeRequest,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Mark a validation finding as fixed.
    """
    # Validate authentication
    if not authorization or not authorization.startswith("Bearer "):
        raise UnauthorizedException("Missing or invalid authorization token")
    
    # Extract user info from JWT token
    token = authorization.split(" ")[1]
    payload = decode_token(token)
    
    if not payload:
        raise UnauthorizedException("Invalid or expired token")
    
    user_id = payload.get("sub")
    hospital_id = payload.get("hospital_id")
    
    if not user_id or not hospital_id:
        raise UnauthorizedException("Token missing required user information")
    
    try:
        validation_service = get_validation_service(db)
        
        finding = validation_service.mark_finding_fixed(
            finding_id=request.finding_id,
            user_id=user_id,
            hospital_id=hospital_id
        )
        
        if not finding:
            raise NotFoundException("Finding not found")
        
        response_data, status_code = APIResponse.success(
            message="Finding marked as fixed successfully",
            data={"finding_id": finding.id}
        )
        
        return response_data
        
    except NotFoundException:
        raise
    except Exception as e:
        logger.error(f"[MARK_FIXED_ERROR] Finding ID: {request.finding_id}, Error: {str(e)}")
        raise APIValidationException(f"Failed to mark finding as fixed: {str(e)}")


@router.post("/findings/dismiss")
async def dismiss_finding(
    request: FindingDismissRequest,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Dismiss a validation finding with optional reason.
    """
    # Validate authentication
    if not authorization or not authorization.startswith("Bearer "):
        raise UnauthorizedException("Missing or invalid authorization token")
    
    # Extract user info from JWT token
    token = authorization.split(" ")[1]
    payload = decode_token(token)
    
    if not payload:
        raise UnauthorizedException("Invalid or expired token")
    
    user_id = payload.get("sub")
    hospital_id = payload.get("hospital_id")
    
    if not user_id or not hospital_id:
        raise UnauthorizedException("Token missing required user information")
    
    try:
        validation_service = get_validation_service(db)
        
        finding = validation_service.dismiss_finding(
            finding_id=request.finding_id,
            user_id=user_id,
            hospital_id=hospital_id,
            reason=request.reason
        )
        
        if not finding:
            raise NotFoundException("Finding not found")
        
        response_data, status_code = APIResponse.success(
            message="Finding dismissed successfully",
            data={"finding_id": finding.id}
        )
        
        return response_data
        
    except NotFoundException:
        raise
    except Exception as e:
        logger.error(f"[DISMISS_FINDING_ERROR] Finding ID: {request.finding_id}, Error: {str(e)}")
        raise APIValidationException(f"Failed to dismiss finding: {str(e)}")
