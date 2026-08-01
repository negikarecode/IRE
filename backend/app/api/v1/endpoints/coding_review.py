import logging
from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import decode_token
from app.core.api_response import APIResponse
from app.core.exceptions import UnauthorizedException, NotFoundException, ValidationException as APIValidationException
from app.infrastructure.services.coding_review_service import get_coding_review_service
from app.infrastructure.db.models.claim import CodingReviewSeverity

logger = logging.getLogger("coding_review_api")
router = APIRouter()


class CodingReviewRequest(BaseModel):
    claim_id: str
    clinical_data: dict
    ocr_text: Optional[str] = None
    document_id: Optional[str] = None


class FindingAcknowledgeRequest(BaseModel):
    finding_id: str
    reason: Optional[str] = None


class FindingDismissRequest(BaseModel):
    finding_id: str
    reason: Optional[str] = None


class CodingReviewResponse(BaseModel):
    claim_id: str
    hospital_id: str
    icd_codes_reviewed: int
    cpt_codes_reviewed: int
    total_findings: int
    findings: List[dict]
    summary: dict
    can_submit: bool


class CodingFindingResponse(BaseModel):
    id: str
    claim_id: str
    code_type: str
    code_value: str
    modifier: Optional[str]
    severity: str
    category: str
    confidence: float
    detected_issue: str
    correct_coding_recommendation: Optional[str]
    reference_document: Optional[str]
    expected_financial_impact: Optional[float]
    medical_evidence: Optional[dict]
    status: str
    created_at: str


class CodingSummaryResponse(BaseModel):
    claim_id: str
    total_findings: int
    critical_findings: int
    high_findings: int
    medium_findings: int
    low_findings: int
    icd_codes_reviewed: int
    cpt_codes_reviewed: int
    total_financial_impact: Optional[float]
    impact_currency: str
    overall_status: str
    overall_confidence: float
    reviewed_at: str


@router.post("/review")
async def review_claim_coding(
    request: CodingReviewRequest,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Perform comprehensive medical coding review for a claim.
    
    Reviews:
    - ICD codes (invalid, deleted codes)
    - CPT codes (invalid, missing modifiers)
    - Code combinations (incompatible pairs)
    - Diagnosis-procedure compatibility
    - Bundling issues
    - Medical necessity
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
        coding_review_service = get_coding_review_service(db)
        
        result = coding_review_service.review_claim_coding(
            claim_id=request.claim_id,
            hospital_id=hospital_id,
            clinical_data=request.clinical_data,
            ocr_text=request.ocr_text,
            document_id=request.document_id
        )
        
        logger.info(f"[CODING_REVIEW_API] Claim ID: {request.claim_id}, Findings: {result['total_findings']}")
        
        response_data, status_code = APIResponse.success(
            message="Coding review completed successfully",
            data=result
        )
        
        return response_data
        
    except Exception as e:
        logger.error(f"[CODING_REVIEW_API_ERROR] Claim ID: {request.claim_id}, Error: {str(e)}")
        raise APIValidationException(f"Failed to review coding: {str(e)}")


@router.post("/re-review")
async def re_review_claim_coding(
    request: CodingReviewRequest,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Re-review a claim (clears old findings and creates new ones).
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
        coding_review_service = get_coding_review_service(db)
        
        result = coding_review_service.re_review_claim(
            claim_id=request.claim_id,
            hospital_id=hospital_id,
            clinical_data=request.clinical_data,
            ocr_text=request.ocr_text,
            document_id=request.document_id
        )
        
        logger.info(f"[CODING_RE_REVIEW_API] Claim ID: {request.claim_id}, Findings: {result['total_findings']}")
        
        response_data, status_code = APIResponse.success(
            message="Coding re-review completed successfully",
            data=result
        )
        
        return response_data
        
    except Exception as e:
        logger.error(f"[CODING_RE_REVIEW_API_ERROR] Claim ID: {request.claim_id}, Error: {str(e)}")
        raise APIValidationException(f"Failed to re-review claim coding: {str(e)}")


@router.get("/claims/{claim_id}/findings")
async def get_claim_findings(
    claim_id: str,
    code_type: Optional[str] = None,
    severity: Optional[str] = None,
    status: Optional[str] = None,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Get coding review findings for a claim.
    
    Query parameters:
    - code_type: Filter by code type (ICD, CPT, HCPCS)
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
        coding_review_service = get_coding_review_service(db)
        
        findings = coding_review_service.get_findings_for_claim(
            claim_id=claim_id,
            hospital_id=hospital_id,
            code_type=code_type,
            severity=severity,
            status=status
        )
        
        response_data, status_code = APIResponse.success(
            message="Coding findings retrieved successfully",
            data=[{
                "id": f.id,
                "claim_id": f.claim_id,
                "code_type": f.code_type,
                "code_value": f.code_value,
                "modifier": f.modifier,
                "severity": f.severity,
                "category": f.category,
                "confidence": f.confidence,
                "detected_issue": f.detected_issue,
                "correct_coding_recommendation": f.correct_coding_recommendation,
                "reference_document": f.reference_document,
                "expected_financial_impact": f.expected_financial_impact,
                "medical_evidence": f.medical_evidence,
                "status": f.status,
                "created_at": f.created_at.isoformat() if f.created_at else None
            } for f in findings]
        )
        
        return response_data
        
    except Exception as e:
        logger.error(f"[GET_CODING_FINDINGS_ERROR] Claim ID: {claim_id}, Error: {str(e)}")
        raise APIValidationException(f"Failed to retrieve findings: {str(e)}")


@router.get("/claims/{claim_id}/summary")
async def get_claim_summary(
    claim_id: str,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Get coding review summary for a claim.
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
        coding_review_service = get_coding_review_service(db)
        
        summary = coding_review_service.get_summary_for_claim(claim_id, hospital_id)
        
        if not summary:
            raise NotFoundException("Coding review summary not found")
        
        response_data, status_code = APIResponse.success(
            message="Coding summary retrieved successfully",
            data={
                "claim_id": summary.claim_id,
                "total_findings": summary.total_findings,
                "critical_findings": summary.critical_findings,
                "high_findings": summary.high_findings,
                "medium_findings": summary.medium_findings,
                "low_findings": summary.low_findings,
                "icd_codes_reviewed": summary.icd_codes_reviewed,
                "cpt_codes_reviewed": summary.cpt_codes_reviewed,
                "total_financial_impact": summary.total_financial_impact,
                "impact_currency": summary.impact_currency,
                "overall_status": summary.overall_status,
                "overall_confidence": summary.overall_confidence or 0.0,
                "reviewed_at": summary.reviewed_at.isoformat() if summary.reviewed_at else None
            }
        )
        
        return response_data
        
    except NotFoundException:
        raise
    except Exception as e:
        logger.error(f"[GET_CODING_SUMMARY_ERROR] Claim ID: {claim_id}, Error: {str(e)}")
        raise APIValidationException(f"Failed to retrieve coding summary: {str(e)}")


@router.post("/findings/acknowledge")
async def acknowledge_finding(
    request: FindingAcknowledgeRequest,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Acknowledge a coding review finding.
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
        coding_review_service = get_coding_review_service(db)
        
        finding = coding_review_service.acknowledge_finding(
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
        logger.error(f"[ACKNOWLEDGE_CODING_FINDING_ERROR] Finding ID: {request.finding_id}, Error: {str(e)}")
        raise APIValidationException(f"Failed to acknowledge finding: {str(e)}")


@router.post("/findings/fixed")
async def mark_finding_fixed(
    request: FindingAcknowledgeRequest,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Mark a coding review finding as fixed.
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
        coding_review_service = get_coding_review_service(db)
        
        finding = coding_review_service.mark_finding_fixed(
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
        logger.error(f"[MARK_CODING_FIXED_ERROR] Finding ID: {request.finding_id}, Error: {str(e)}")
        raise APIValidationException(f"Failed to mark finding as fixed: {str(e)}")


@router.post("/findings/dismiss")
async def dismiss_finding(
    request: FindingDismissRequest,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Dismiss a coding review finding with optional reason.
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
        coding_review_service = get_coding_review_service(db)
        
        finding = coding_review_service.dismiss_finding(
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
        logger.error(f"[DISMISS_CODING_FINDING_ERROR] Finding ID: {request.finding_id}, Error: {str(e)}")
        raise APIValidationException(f"Failed to dismiss finding: {str(e)}")
