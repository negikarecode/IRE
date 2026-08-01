import logging
from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import decode_token
from app.core.api_response import APIResponse
from app.core.exceptions import UnauthorizedException, NotFoundException, ValidationException as APIValidationException
from app.infrastructure.services.denial_prediction_service import get_denial_prediction_service
from app.infrastructure.db.models.claim import DenialRiskScore

logger = logging.getLogger("denial_prediction_api")
router = APIRouter()


class DenialPredictionRequest(BaseModel):
    claim_id: str
    documents: List[dict]
    clinical_data: dict
    claim_data: dict
    validation_findings: Optional[List[dict]] = None
    coding_review_findings: Optional[List[dict]] = None
    patient_id: Optional[str] = None


class DenialPredictionResponse(BaseModel):
    claim_id: str
    hospital_id: str
    denial_probability: float
    risk_score: str
    confidence: float
    estimated_financial_exposure: Optional[float]
    exposure_currency: str
    claim_amount: Optional[float]
    predicted_denial_reasons: List[dict]
    contributing_factors: List[dict]
    risk_factors: List[dict]


class PredictionSummaryResponse(BaseModel):
    claim_id: str
    denial_probability: float
    risk_score: str
    confidence: float
    estimated_financial_exposure: Optional[float]
    claim_amount: Optional[float]
    prediction_timestamp: str


@router.post("/predict")
async def predict_denial_probability(
    request: DenialPredictionRequest,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Predict the probability that a claim will be denied.
    
    Analyzes:
    - Missing documentation
    - Authorization status
    - Coding issues
    - Insurance-specific rules
    - Historical denial patterns
    - Clinical inconsistencies
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
        denial_prediction_service = get_denial_prediction_service(db)
        
        result = denial_prediction_service.predict_denial_probability(
            claim_id=request.claim_id,
            hospital_id=hospital_id,
            documents=request.documents,
            clinical_data=request.clinical_data,
            claim_data=request.claim_data,
            validation_findings=request.validation_findings,
            coding_review_findings=request.coding_review_findings,
            patient_id=request.patient_id
        )
        
        logger.info(f"[DENIAL_PREDICTION_API] Claim ID: {request.claim_id}, Probability: {result['denial_probability']:.2f}, Risk: {result['risk_score']}")
        
        response_data, status_code = APIResponse.success(
            message="Denial prediction completed successfully",
            data=result
        )
        
        return response_data
        
    except Exception as e:
        logger.error(f"[DENIAL_PREDICTION_API_ERROR] Claim ID: {request.claim_id}, Error: {str(e)}")
        raise APIValidationException(f"Failed to predict denial probability: {str(e)}")


@router.post("/re-predict")
async def re_predict_denial_probability(
    request: DenialPredictionRequest,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Re-predict denial probability (updates existing prediction).
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
        denial_prediction_service = get_denial_prediction_service(db)
        
        result = denial_prediction_service.re_predict(
            claim_id=request.claim_id,
            hospital_id=hospital_id,
            documents=request.documents,
            clinical_data=request.clinical_data,
            claim_data=request.claim_data,
            validation_findings=request.validation_findings,
            coding_review_findings=request.coding_review_findings,
            patient_id=request.patient_id
        )
        
        logger.info(f"[DENIAL_RE_PREDICTION_API] Claim ID: {request.claim_id}, Probability: {result['denial_probability']:.2f}")
        
        response_data, status_code = APIResponse.success(
            message="Denial re-prediction completed successfully",
            data=result
        )
        
        return response_data
        
    except Exception as e:
        logger.error(f"[DENIAL_RE_PREDICTION_API_ERROR] Claim ID: {request.claim_id}, Error: {str(e)}")
        raise APIValidationException(f"Failed to re-predict denial probability: {str(e)}")


@router.get("/claims/{claim_id}/prediction")
async def get_claim_prediction(
    claim_id: str,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Get denial prediction summary for a claim.
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
        denial_prediction_service = get_denial_prediction_service(db)
        
        prediction = denial_prediction_service.get_prediction_for_claim(claim_id, hospital_id)
        
        if not prediction:
            raise NotFoundException("Denial prediction not found")
        
        response_data, status_code = APIResponse.success(
            message="Denial prediction retrieved successfully",
            data={
                "claim_id": prediction.claim_id,
                "denial_probability": prediction.denial_probability,
                "risk_score": prediction.risk_score,
                "confidence": prediction.confidence,
                "estimated_financial_exposure": prediction.estimated_financial_exposure,
                "claim_amount": prediction.claim_amount,
                "prediction_timestamp": prediction.prediction_timestamp.isoformat() if prediction.prediction_timestamp else None
            }
        )
        
        return response_data
        
    except NotFoundException:
        raise
    except Exception as e:
        logger.error(f"[GET_DENIAL_PREDICTION_ERROR] Claim ID: {claim_id}, Error: {str(e)}")
        raise APIValidationException(f"Failed to retrieve prediction: {str(e)}")


@router.get("/claims/{claim_id}/full-prediction")
async def get_full_claim_prediction(
    claim_id: str,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Get full denial prediction details including all risk factors.
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
        denial_prediction_service = get_denial_prediction_service(db)
        
        prediction = denial_prediction_service.get_prediction_for_claim(claim_id, hospital_id)
        
        if not prediction:
            raise NotFoundException("Denial prediction not found")
        
        # Reconstruct risk factors from individual scores
        risk_factors = [
            {
                "factor_name": "missing_documentation",
                "score": prediction.missing_documentation_score,
                "weight": 0.25,
                "explanation": "Missing documentation risk factor"
            },
            {
                "factor_name": "authorization",
                "score": prediction.authorization_score,
                "weight": 0.20,
                "explanation": "Authorization risk factor"
            },
            {
                "factor_name": "coding",
                "score": prediction.coding_score,
                "weight": 0.25,
                "explanation": "Coding risk factor"
            },
            {
                "factor_name": "insurance_rules",
                "score": prediction.insurance_rules_score,
                "weight": 0.15,
                "explanation": "Insurance-specific rules risk factor"
            },
            {
                "factor_name": "historical_patterns",
                "score": prediction.historical_patterns_score,
                "weight": 0.10,
                "explanation": "Historical patterns risk factor"
            },
            {
                "factor_name": "clinical_inconsistencies",
                "score": prediction.clinical_inconsistencies_score,
                "weight": 0.05,
                "explanation": "Clinical inconsistencies risk factor"
            }
        ]
        
        response_data, status_code = APIResponse.success(
            message="Full denial prediction retrieved successfully",
            data={
                "claim_id": prediction.claim_id,
                "hospital_id": prediction.hospital_id,
                "denial_probability": prediction.denial_probability,
                "risk_score": prediction.risk_score,
                "confidence": prediction.confidence,
                "estimated_financial_exposure": prediction.estimated_financial_exposure,
                "exposure_currency": prediction.exposure_currency,
                "claim_amount": prediction.claim_amount,
                "predicted_denial_reasons": prediction.predicted_denial_reasons or [],
                "contributing_factors": risk_factors,
                "risk_factors": risk_factors
            }
        )
        
        return response_data
        
    except NotFoundException:
        raise
    except Exception as e:
        logger.error(f"[GET_FULL_DENIAL_PREDICTION_ERROR] Claim ID: {claim_id}, Error: {str(e)}")
        raise APIValidationException(f"Failed to retrieve full prediction: {str(e)}")
