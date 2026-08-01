import logging
from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import decode_token
from app.core.api_response import APIResponse
from app.core.exceptions import UnauthorizedException, NotFoundException, ValidationException as APIValidationException
from app.infrastructure.services.revenue_leakage_service import get_revenue_leakage_service
from app.infrastructure.db.models.claim import RevenueLeakageCategory

logger = logging.getLogger("revenue_leakage_api")
router = APIRouter()


class RevenueLeakageRequest(BaseModel):
    claim_id: str
    clinical_data: dict
    claim_amount: Optional[float] = None
    ocr_text: Optional[str] = None
    document_id: Optional[str] = None


class FindingAcknowledgeRequest(BaseModel):
    finding_id: str
    reason: Optional[str] = None


class FindingRecoverRequest(BaseModel):
    finding_id: str
    recovered_amount: Optional[float] = None


class FindingDismissRequest(BaseModel):
    finding_id: str
    reason: Optional[str] = None


class RevenueLeakageResponse(BaseModel):
    claim_id: str
    hospital_id: str
    total_findings: int
    findings: List[dict]
    summary: dict


class LeakageFindingResponse(BaseModel):
    id: str
    claim_id: str
    category: str
    confidence: float
    estimated_recoverable_revenue: Optional[float]
    revenue_currency: str
    description: str
    recommended_correction: Optional[str]
    supporting_evidence: Optional[dict]
    affected_document: Optional[str]
    affected_code: Optional[str]
    status: str
    created_at: str


class LeakageSummaryResponse(BaseModel):
    claim_id: str
    total_findings: int
    total_recoverable_revenue: Optional[float]
    revenue_currency: str
    category_breakdown: dict
    recovered_amount: float
    recovery_percentage: Optional[float]
    detection_timestamp: str


@router.post("/detect")
async def detect_revenue_leakage(
    request: RevenueLeakageRequest,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Detect revenue leakage in a claim.
    
    Analyzes:
    - Underbilling
    - Missing procedures
    - Missing modifiers
    - Missed diagnoses
    - Missing implants
    - Incomplete charges
    - Incorrect coding
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
        revenue_leakage_service = get_revenue_leakage_service(db)
        
        result = revenue_leakage_service.detect_revenue_leakage(
            claim_id=request.claim_id,
            hospital_id=hospital_id,
            clinical_data=request.clinical_data,
            claim_amount=request.claim_amount,
            ocr_text=request.ocr_text,
            document_id=request.document_id
        )
        
        logger.info(f"[REVENUE_LEAKAGE_API] Claim ID: {request.claim_id}, Findings: {result['total_findings']}, Recoverable: ₹{result['summary'].get('total_recoverable_revenue', 0):.2f}")
        
        response_data, status_code = APIResponse.success(
            message="Revenue leakage detection completed successfully",
            data=result
        )
        
        return response_data
        
    except Exception as e:
        logger.error(f"[REVENUE_LEAKAGE_API_ERROR] Claim ID: {request.claim_id}, Error: {str(e)}")
        raise APIValidationException(f"Failed to detect revenue leakage: {str(e)}")


@router.post("/re-detect")
async def re_detect_revenue_leakage(
    request: RevenueLeakageRequest,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Re-detect revenue leakage (clears old findings and creates new ones).
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
        revenue_leakage_service = get_revenue_leakage_service(db)
        
        result = revenue_leakage_service.re_detect(
            claim_id=request.claim_id,
            hospital_id=hospital_id,
            clinical_data=request.clinical_data,
            claim_amount=request.claim_amount,
            ocr_text=request.ocr_text,
            document_id=request.document_id
        )
        
        logger.info(f"[REVENUE_LEAKAGE_RE_DETECT_API] Claim ID: {request.claim_id}, Findings: {result['total_findings']}")
        
        response_data, status_code = APIResponse.success(
            message="Revenue leakage re-detection completed successfully",
            data=result
        )
        
        return response_data
        
    except Exception as e:
        logger.error(f"[REVENUE_LEAKAGE_RE_DETECT_API_ERROR] Claim ID: {request.claim_id}, Error: {str(e)}")
        raise APIValidationException(f"Failed to re-detect revenue leakage: {str(e)}")


@router.get("/claims/{claim_id}/findings")
async def get_claim_findings(
    claim_id: str,
    category: Optional[str] = None,
    status: Optional[str] = None,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Get revenue leakage findings for a claim.
    
    Query parameters:
    - category: Filter by category (underbilling, missing_procedure, etc.)
    - status: Filter by status (open, acknowledged, recovered, dismissed)
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
        revenue_leakage_service = get_revenue_leakage_service(db)
        
        findings = revenue_leakage_service.get_findings_for_claim(
            claim_id=claim_id,
            hospital_id=hospital_id,
            category=category,
            status=status
        )
        
        response_data, status_code = APIResponse.success(
            message="Revenue leakage findings retrieved successfully",
            data=[{
                "id": f.id,
                "claim_id": f.claim_id,
                "category": f.category,
                "confidence": f.confidence,
                "estimated_recoverable_revenue": f.estimated_recoverable_revenue,
                "revenue_currency": f.revenue_currency,
                "description": f.description,
                "recommended_correction": f.recommended_correction,
                "supporting_evidence": f.supporting_evidence,
                "affected_document": f.affected_document,
                "affected_code": f.affected_code,
                "status": f.status,
                "created_at": f.created_at.isoformat() if f.created_at else None
            } for f in findings]
        )
        
        return response_data
        
    except Exception as e:
        logger.error(f"[GET_LEAKAGE_FINDINGS_ERROR] Claim ID: {claim_id}, Error: {str(e)}")
        raise APIValidationException(f"Failed to retrieve findings: {str(e)}")


@router.get("/claims/{claim_id}/summary")
async def get_claim_summary(
    claim_id: str,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Get revenue leakage summary for a claim.
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
        revenue_leakage_service = get_revenue_leakage_service(db)
        
        summary = revenue_leakage_service.get_summary_for_claim(claim_id, hospital_id)
        
        if not summary:
            raise NotFoundException("Revenue leakage summary not found")
        
        response_data, status_code = APIResponse.success(
            message="Revenue leakage summary retrieved successfully",
            data={
                "claim_id": summary.claim_id,
                "total_findings": summary.total_findings,
                "total_recoverable_revenue": summary.total_recoverable_revenue,
                "revenue_currency": summary.revenue_currency,
                "category_breakdown": {
                    "underbilling": summary.underbilling_count,
                    "missing_procedure": summary.missing_procedure_count,
                    "missing_modifier": summary.missing_modifier_count,
                    "missed_diagnosis": summary.missed_diagnosis_count,
                    "missing_implant": summary.missing_implant_count,
                    "incomplete_charges": summary.incomplete_charges_count,
                    "incorrect_coding": summary.incorrect_coding_count
                },
                "recovered_amount": summary.recovered_amount,
                "recovery_percentage": summary.recovery_percentage,
                "detection_timestamp": summary.detection_timestamp.isoformat() if summary.detection_timestamp else None
            }
        )
        
        return response_data
        
    except NotFoundException:
        raise
    except Exception as e:
        logger.error(f"[GET_LEAKAGE_SUMMARY_ERROR] Claim ID: {claim_id}, Error: {str(e)}")
        raise APIValidationException(f"Failed to retrieve summary: {str(e)}")


@router.post("/findings/acknowledge")
async def acknowledge_finding(
    request: FindingAcknowledgeRequest,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Acknowledge a revenue leakage finding.
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
        revenue_leakage_service = get_revenue_leakage_service(db)
        
        finding = revenue_leakage_service.acknowledge_finding(
            finding_id=request.finding_id,
            user_id=user_id,
            hospital_id=hospital_id
        )
        
        if not finding:
            raise NotFoundException("Finding not found")
        
        return {
            "success": True,
            "message": "Finding acknowledged",
            "data": {"finding_id": finding.id}
        }
        
    except (UnauthorizedException, NotFoundException):
        raise
    except Exception as e:
        logger.error(f"[ACKNOWLEDGE_LEAKAGE_FINDING_ERROR] Finding ID: {request.finding_id}, Error: {str(e)}")
        raise APIValidationException(f"Failed to acknowledge finding: {str(e)}")


@router.post("/findings/recovered")
async def mark_finding_recovered(
    request: FindingRecoverRequest,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Mark a revenue leakage finding as recovered.
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
        revenue_leakage_service = get_revenue_leakage_service(db)
        
        finding = revenue_leakage_service.mark_finding_recovered(
            finding_id=request.finding_id,
            user_id=user_id,
            hospital_id=hospital_id,
            recovered_amount=request.recovered_amount
        )
        
        if not finding:
            raise NotFoundException("Finding not found")
        
        return {
            "success": True,
            "message": "Finding marked as recovered",
            "data": {
                "finding_id": finding.id,
                "recovered_amount": finding.recovered_amount
            }
        }
        
    except (UnauthorizedException, NotFoundException):
        raise
    except Exception as e:
        logger.error(f"[MARK_RECOVERED_ERROR] Finding ID: {request.finding_id}, Error: {str(e)}")
        raise APIValidationException(f"Failed to mark finding as recovered: {str(e)}")


@router.post("/findings/dismiss")
async def dismiss_finding(
    request: FindingDismissRequest,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Dismiss a revenue leakage finding with optional reason.
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
        revenue_leakage_service = get_revenue_leakage_service(db)
        
        finding = revenue_leakage_service.dismiss_finding(
            finding_id=request.finding_id,
            user_id=user_id,
            hospital_id=hospital_id,
            reason=request.reason
        )
        
        if not finding:
            raise NotFoundException("Finding not found")
        
        return {
            "success": True,
            "message": "Finding dismissed",
            "data": {"finding_id": finding.id}
        }
        
    except (UnauthorizedException, NotFoundException):
        raise
    except Exception as e:
        logger.error(f"[DISMISS_LEAKAGE_FINDING_ERROR] Finding ID: {request.finding_id}, Error: {str(e)}")
        raise APIValidationException(f"Failed to dismiss finding: {str(e)}")
