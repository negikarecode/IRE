import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.infrastructure.db.models.claim import (
    DenialPredictionModel, DenialRiskScore
)
from app.infrastructure.predictors.denial_risk_factors import (
    MissingDocumentationRiskFactor,
    AuthorizationRiskFactor,
    CodingRiskFactor,
    InsuranceRulesRiskFactor,
    HistoricalPatternsRiskFactor,
    ClinicalInconsistenciesRiskFactor,
    RiskFactorResult
)
from app.infrastructure.base.ai_recommendation import RecommendationBuilder

logger = logging.getLogger("denial_prediction_service")


class DenialPredictionService:
    """Service for predicting claim denial probability"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def predict_denial_probability(
        self,
        claim_id: str,
        hospital_id: str,
        documents: List[Dict[str, Any]],
        clinical_data: Dict[str, Any],
        claim_data: Dict[str, Any],
        validation_findings: List[Dict] = None,
        coding_review_findings: List[Dict] = None,
        patient_id: str = None
    ) -> Dict[str, Any]:
        """
        Predict the probability that a claim will be denied.
        
        Args:
            claim_id: Claim ID for tracking
            hospital_id: Hospital ID for access control
            documents: List of uploaded documents
            clinical_data: Normalized clinical data
            claim_data: Claim data including insurance information
            validation_findings: Validation findings from claim validation
            coding_review_findings: Coding review findings
            patient_id: Patient ID for historical patterns
            
        Returns:
            dict with denial prediction results
        """
        logger.info(f"[DENIAL_PREDICTION_START] Claim ID: {claim_id}")
        
        # Calculate all risk factors
        risk_factors = []
        
        # 1. Missing Documentation Risk
        doc_risk = MissingDocumentationRiskFactor.calculate(documents, validation_findings)
        risk_factors.append(doc_risk)
        
        # 2. Authorization Risk
        auth_risk = AuthorizationRiskFactor.calculate(clinical_data, validation_findings)
        risk_factors.append(auth_risk)
        
        # 3. Coding Risk
        coding_risk = CodingRiskFactor.calculate(coding_review_findings, clinical_data)
        risk_factors.append(coding_risk)
        
        # 4. Insurance Rules Risk
        insurance_risk = InsuranceRulesRiskFactor.calculate(clinical_data, claim_data)
        risk_factors.append(insurance_risk)
        
        # 5. Historical Patterns Risk
        historical_risk = HistoricalPatternsRiskFactor.calculate(hospital_id, patient_id, self.db)
        risk_factors.append(historical_risk)
        
        # 6. Clinical Inconsistencies Risk
        clinical_risk = ClinicalInconsistenciesRiskFactor.calculate(clinical_data, validation_findings)
        risk_factors.append(clinical_risk)
        
        # Calculate weighted denial probability
        denial_probability = self._calculate_weighted_probability(risk_factors)
        
        # Determine risk score category
        risk_score = self._determine_risk_score(denial_probability)
        
        # Calculate overall confidence
        confidence = self._calculate_confidence(risk_factors)
        
        # Calculate financial exposure
        claim_amount = clinical_data.get("bill_amount")
        estimated_exposure = self._calculate_financial_exposure(
            denial_probability, claim_amount
        )
        
        # Generate predicted denial reasons
        predicted_denial_reasons = self._generate_denial_reasons(risk_factors)
        
        # Generate top contributing factors
        contributing_factors = self._generate_contributing_factors(risk_factors)
        
        # Store prediction in database
        self._store_prediction(
            claim_id,
            hospital_id,
            denial_probability,
            risk_score,
            confidence,
            estimated_exposure,
            claim_amount,
            predicted_denial_reasons,
            contributing_factors,
            risk_factors
        )
        
        logger.info(f"[DENIAL_PREDICTION_COMPLETE] Claim ID: {claim_id}, Probability: {denial_probability:.2f}, Risk: {risk_score}")
        
        # Convert risk factors to standardized AI recommendation format
        standardized_factors = [
            RecommendationBuilder.from_denial_factor(rf.to_dict()).to_dict()
            for rf in risk_factors
        ]
        
        return {
            "claim_id": claim_id,
            "hospital_id": hospital_id,
            "denial_probability": denial_probability,
            "risk_score": risk_score,
            "confidence": confidence,
            "estimated_financial_exposure": estimated_exposure,
            "exposure_currency": "INR",
            "claim_amount": claim_amount,
            "predicted_denial_reasons": predicted_denial_reasons,
            "contributing_factors": standardized_factors,
            "risk_factors": [rf.to_dict() for rf in risk_factors]
        }
    
    def _calculate_weighted_probability(self, risk_factors: List[RiskFactorResult]) -> float:
        """Calculate weighted denial probability from risk factors"""
        weighted_sum = 0.0
        total_weight = 0.0
        
        for factor in risk_factors:
            weighted_sum += factor.score * factor.weight
            total_weight += factor.weight
        
        return weighted_sum / total_weight if total_weight > 0 else 0.5
    
    def _determine_risk_score(self, probability: float) -> str:
        """Determine risk score category from probability"""
        if probability < 0.2:
            return DenialRiskScore.LOW.value
        elif probability < 0.5:
            return DenialRiskScore.MEDIUM.value
        elif probability < 0.75:
            return DenialRiskScore.HIGH.value
        else:
            return DenialRiskScore.CRITICAL.value
    
    def _calculate_confidence(self, risk_factors: List[RiskFactorResult]) -> float:
        """Calculate overall confidence in prediction"""
        # Confidence based on consistency of risk factors
        scores = [rf.score for rf in risk_factors]
        
        if not scores:
            return 0.5
        
        # Calculate variance (lower variance = higher confidence)
        mean_score = sum(scores) / len(scores)
        variance = sum((s - mean_score) ** 2 for s in scores) / len(scores)
        
        # Convert variance to confidence (inverse relationship)
        confidence = max(0.5, 1.0 - (variance / 0.25))  # Normalize variance
        
        return min(1.0, confidence)
    
    def _calculate_financial_exposure(
        self,
        denial_probability: float,
        claim_amount: Any
    ) -> Optional[float]:
        """Calculate estimated financial exposure"""
        if not claim_amount:
            return None
        
        try:
            amount = float(claim_amount)
            return amount * denial_probability
        except (ValueError, TypeError):
            return None
    
    def _generate_denial_reasons(self, risk_factors: List[RiskFactorResult]) -> List[Dict[str, Any]]:
        """Generate predicted denial reasons with weights"""
        reasons = []
        
        # Sort risk factors by score (descending)
        sorted_factors = sorted(risk_factors, key=lambda rf: rf.score, reverse=True)
        
        for factor in sorted_factors:
            if factor.score > 0.3:  # Only include significant factors
                # Extract denial reasons from contributing details
                for detail in factor.contributing_details:
                    if "denial_reason" in detail:
                        reasons.append({
                            "reason": detail["denial_reason"],
                            "weight": factor.score,
                            "source_factor": factor.factor_name,
                            "explanation": detail.get("impact", "")
                        })
        
        return reasons
    
    def _generate_contributing_factors(self, risk_factors: List[RiskFactorResult]) -> List[Dict[str, Any]]:
        """Generate top contributing factors with explanations"""
        factors = []
        
        # Sort by score (descending)
        sorted_factors = sorted(risk_factors, key=lambda rf: rf.score, reverse=True)
        
        # Take top 5 factors
        for factor in sorted_factors[:5]:
            factors.append({
                "factor_name": factor.factor_name,
                "score": factor.score,
                "weight": factor.weight,
                "explanation": factor.explanation,
                "key_details": factor.contributing_details[:3]  # Top 3 details
            })
        
        return factors
    
    def _store_prediction(
        self,
        claim_id: str,
        hospital_id: str,
        denial_probability: float,
        risk_score: str,
        confidence: float,
        estimated_exposure: Optional[float],
        claim_amount: Any,
        predicted_denial_reasons: List[Dict],
        contributing_factors: List[Dict],
        risk_factors: List[RiskFactorResult]
    ):
        """Store denial prediction in database"""
        try:
            # Create prediction record
            prediction_record = DenialPredictionModel(
                id=str(__import__('uuid').uuid4()),
                claim_id=claim_id,
                hospital_id=hospital_id,
                denial_probability=denial_probability,
                risk_score=risk_score,
                confidence=confidence,
                estimated_financial_exposure=estimated_exposure,
                exposure_currency="INR",
                claim_amount=float(claim_amount) if claim_amount else None,
                predicted_denial_reasons=predicted_denial_reasons,
                contributing_factors=contributing_factors,
                # Store individual risk factor scores
                missing_documentation_score=next((rf.score for rf in risk_factors if rf.factor_name == "missing_documentation"), None),
                authorization_score=next((rf.score for rf in risk_factors if rf.factor_name == "authorization"), None),
                coding_score=next((rf.score for rf in risk_factors if rf.factor_name == "coding"), None),
                insurance_rules_score=next((rf.score for rf in risk_factors if rf.factor_name == "insurance_rules"), None),
                historical_patterns_score=next((rf.score for rf in risk_factors if rf.factor_name == "historical_patterns"), None),
                clinical_inconsistencies_score=next((rf.score for rf in risk_factors if rf.factor_name == "clinical_inconsistencies"), None),
                prediction_timestamp=datetime.now(timezone.utc),
                prediction_model_version="1.0"
            )
            
            # Update existing prediction or create new
            existing = self.db.query(DenialPredictionModel).filter(
                DenialPredictionModel.claim_id == claim_id
            ).first()
            
            if existing:
                existing.denial_probability = denial_probability
                existing.risk_score = risk_score
                existing.confidence = confidence
                existing.estimated_financial_exposure = estimated_exposure
                existing.claim_amount = float(claim_amount) if claim_amount else None
                existing.predicted_denial_reasons = predicted_denial_reasons
                existing.contributing_factors = contributing_factors
                existing.missing_documentation_score = prediction_record.missing_documentation_score
                existing.authorization_score = prediction_record.authorization_score
                existing.coding_score = prediction_record.coding_score
                existing.insurance_rules_score = prediction_record.insurance_rules_score
                existing.historical_patterns_score = prediction_record.historical_patterns_score
                existing.clinical_inconsistencies_score = prediction_record.clinical_inconsistencies_score
                existing.prediction_timestamp = datetime.now(timezone.utc)
                existing.updated_at = datetime.now(timezone.utc)
            else:
                self.db.add(prediction_record)
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"[PREDICTION_STORE_ERROR] Claim ID: {claim_id}, Error: {e}")
            self.db.rollback()
    
    def get_prediction_for_claim(
        self,
        claim_id: str,
        hospital_id: str
    ) -> Optional[DenialPredictionModel]:
        """
        Get denial prediction for a claim.
        
        Args:
            claim_id: Claim ID
            hospital_id: Hospital ID for access control
            
        Returns:
            Denial prediction or None
        """
        return self.db.query(DenialPredictionModel).filter(
            DenialPredictionModel.claim_id == claim_id,
            DenialPredictionModel.hospital_id == hospital_id
        ).first()
    
    def re_predict(
        self,
        claim_id: str,
        hospital_id: str,
        documents: List[Dict[str, Any]],
        clinical_data: Dict[str, Any],
        claim_data: Dict[str, Any],
        validation_findings: List[Dict] = None,
        coding_review_findings: List[Dict] = None,
        patient_id: str = None
    ) -> Dict[str, Any]:
        """
        Re-predict denial probability (updates existing prediction).
        
        Args:
            claim_id: Claim ID
            hospital_id: Hospital ID
            documents: List of documents
            clinical_data: Clinical data
            claim_data: Claim data
            validation_findings: Validation findings
            coding_review_findings: Coding review findings
            patient_id: Patient ID
            
        Returns:
            dict with new prediction results
        """
        logger.info(f"[DENIAL_RE_PREDICTION] Claim ID: {claim_id}")
        
        return self.predict_denial_probability(
            claim_id,
            hospital_id,
            documents,
            clinical_data,
            claim_data,
            validation_findings,
            coding_review_findings,
            patient_id
        )


def get_denial_prediction_service(db: Session) -> DenialPredictionService:
    """Factory function to get denial prediction service instance"""
    return DenialPredictionService(db)
