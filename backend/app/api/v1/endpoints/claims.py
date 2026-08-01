from fastapi import APIRouter, Depends, status, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Dict, Any, Optional
from app.core.database import get_db
from app.core.dependencies import get_tenant_header
from app.application.schemas.domain_schemas import ClaimCreate, ClaimResponse
from app.infrastructure.db.models.claim import ClaimModel
from app.domain.interfaces.i_claim_processor import IClaimProcessor
from app.core.security import decode_token
from app.infrastructure.services.validation_service import get_validation_service
from app.infrastructure.services.coding_review_service import get_coding_review_service
from app.infrastructure.services.denial_prediction_service import get_denial_prediction_service
from app.infrastructure.services.revenue_leakage_service import get_revenue_leakage_service
from app.infrastructure.services.corrected_claim_service import get_corrected_claim_service

router = APIRouter()

class DefaultClaimProcessor(IClaimProcessor):
    """
    Interface implementation stub.
    Zero insurance or claim validation business logic implemented.
    Future domain experts will inject their reasoning engine implementation here.
    """
    async def process_claim(self, tenant_id: str, claim_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "processor_status": "SKIPPED_VALIDATION_STUB",
            "message": "Platform architecture frame. Business logic deferred to pluggable domain engines."
        }

    async def calculate_risk_score(self, tenant_id: str, payload: Dict[str, Any]) -> float:
        return 0.0

def get_claim_processor() -> IClaimProcessor:
    return DefaultClaimProcessor()

from app.core.exceptions import UnauthorizedException

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_claim(
    claim_in: ClaimCreate,
    tenant_id: str = Depends(get_tenant_header),
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
    processor: IClaimProcessor = Depends(get_claim_processor)
):
    # Validate authentication
    if not authorization or not authorization.startswith("Bearer "):
        raise UnauthorizedException(message="Missing or invalid authorization token")
    
    # Extract user info from JWT token
    token = authorization.split(" ")[1]
    payload = decode_token(token)
    
    if not payload:
        raise UnauthorizedException(message="Invalid or expired token")
    
    hospital_id = payload.get("hospital_id")
    user_id = payload.get("sub")
    
    if not hospital_id:
        raise UnauthorizedException(message="Token missing hospital information")
    
    claim = ClaimModel(
        tenant_id=tenant_id,
        patient_id=claim_in.patient_id,
        hospital_id=claim_in.hospital_id,
        external_claim_ref=claim_in.external_claim_ref,
        amount=claim_in.amount,
        raw_payload=claim_in.raw_payload,
        status="PENDING_VALIDATION"
    )
    db.add(claim)
    await db.commit()
    await db.refresh(claim)

    # Perform AI claim validation before submission
    try:
        documents = claim_in.raw_payload.get("documents", [])
        clinical_data_list = claim_in.raw_payload.get("clinical_data", [])
        ocr_texts = claim_in.raw_payload.get("ocr_texts", {})
        
        validation_service = get_validation_service(db)
        validation_result = validation_service.validate_claim(
            claim_id=claim.id,
            hospital_id=hospital_id,
            documents=documents,
            clinical_data_list=clinical_data_list,
            claim_data=claim_in.raw_payload,
            ocr_texts=ocr_texts
        )
        
        if validation_result["can_submit"]:
            claim.status = "VALIDATED"
        else:
            claim.status = "VALIDATION_FAILED"
        
        claim.validation_summary = validation_result["summary"]
        await db.commit()
        await db.refresh(claim)
        
        try:
            primary_clinical_data = clinical_data_list[0] if clinical_data_list else {}
            primary_ocr_text = ocr_texts.get(documents[0].get("document_id"), "") if documents and ocr_texts else None
            
            coding_review_service = get_coding_review_service(db)
            coding_review_result = coding_review_service.review_claim_coding(
                claim_id=claim.id,
                hospital_id=hospital_id,
                clinical_data=primary_clinical_data,
                ocr_text=primary_ocr_text,
                document_id=documents[0].get("document_id") if documents else None
            )
            
            if not coding_review_result["can_submit"]:
                claim.status = "CODING_REVIEW_FAILED"
            
            claim.coding_review_summary = coding_review_result["summary"]
            await db.commit()
            await db.refresh(claim)
        except Exception as coding_error:
            claim.status = "CODING_REVIEW_ERROR"
            await db.commit()
            await db.refresh(claim)
        
        try:
            denial_prediction_service = get_denial_prediction_service(db)
            denial_prediction_result = denial_prediction_service.predict_denial_probability(
                claim_id=claim.id,
                hospital_id=hospital_id,
                documents=documents,
                clinical_data=primary_clinical_data,
                claim_data=claim_in.raw_payload,
                validation_findings=validation_result.get("findings", []) if 'validation_result' in locals() else [],
                coding_review_findings=coding_review_result.get("findings", []) if 'coding_review_result' in locals() else [],
                patient_id=claim_in.patient_id
            )
            
            claim.denial_prediction_summary = {
                "denial_probability": denial_prediction_result["denial_probability"],
                "risk_score": denial_prediction_result["risk_score"],
                "confidence": denial_prediction_result["confidence"],
                "estimated_financial_exposure": denial_prediction_result["estimated_financial_exposure"]
            }
            await db.commit()
            await db.refresh(claim)
        except Exception as denial_error:
            pass
        
        try:
            revenue_leakage_service = get_revenue_leakage_service(db)
            revenue_leakage_result = revenue_leakage_service.detect_revenue_leakage(
                claim_id=claim.id,
                hospital_id=hospital_id,
                clinical_data=primary_clinical_data,
                claim_amount=primary_clinical_data.get("bill_amount"),
                ocr_text=primary_ocr_text,
                document_id=documents[0].get("document_id") if documents else None
            )
            
            claim.revenue_leakage_summary = {
                "total_findings": revenue_leakage_result["total_findings"],
                "total_recoverable_revenue": revenue_leakage_result["summary"].get("total_recoverable_revenue"),
                "category_breakdown": revenue_leakage_result["summary"].get("category_breakdown")
            }
            await db.commit()
            await db.refresh(claim)
        except Exception as leakage_error:
            pass
        
        try:
            corrected_claim_service = get_corrected_claim_service(db)
            corrected_claim_result = corrected_claim_service.generate_corrected_claim(
                claim_id=claim.id,
                hospital_id=hospital_id,
                original_claim_data=claim_in.raw_payload,
                validation_findings=validation_result.get("findings", []) if 'validation_result' in locals() else [],
                coding_findings=coding_review_result.get("findings", []) if 'coding_review_result' in locals() else [],
                leakage_findings=revenue_leakage_result.get("findings", []) if 'revenue_leakage_result' in locals() else []
            )
            
            claim.corrected_claim_preview_id = corrected_claim_result["preview_id"]
            await db.commit()
            await db.refresh(claim)
        except Exception as corrected_claim_error:
            pass
        
        adjudication_output = await processor.process_claim(tenant_id, claim.id, claim_in.raw_payload)
        claim.adjudication_output = adjudication_output
        await db.commit()
        await db.refresh(claim)
    except Exception as validation_error:
        claim.status = "VALIDATION_ERROR"
        await db.commit()
        await db.refresh(claim)

    claim_data = ClaimResponse.model_validate(claim)
    return {
        "success": True,
        "message": "Claim created successfully",
        "data": claim_data.model_dump()
    }

@router.get("/", status_code=status.HTTP_200_OK)
async def list_claims(
    tenant_id: str = Depends(get_tenant_header),
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
):
    query = select(ClaimModel).where(ClaimModel.tenant_id == tenant_id)
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        payload = decode_token(token)
        if payload and payload.get("hospital_id"):
            query = query.where(ClaimModel.hospital_id == payload.get("hospital_id"))
    result = await db.execute(query)
    claims = result.scalars().all()
    data = [ClaimResponse.model_validate(c).model_dump() for c in claims]
    return {
        "success": True,
        "message": "Claims retrieved successfully",
        "data": data
    }
