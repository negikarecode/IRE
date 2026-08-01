import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from app.infrastructure.db.models.claim import DenialRiskScore

logger = logging.getLogger("denial_risk_factors")


class RiskFactorResult:
    """Represents a single risk factor calculation result"""
    
    def __init__(
        self,
        factor_name: str,
        score: float,  # 0.0 to 1.0
        weight: float,  # Importance weight in overall prediction
        explanation: str,
        contributing_details: List[Dict[str, Any]] = None
    ):
        self.factor_name = factor_name
        self.score = score
        self.weight = weight
        self.explanation = explanation
        self.contributing_details = contributing_details or []
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "factor_name": self.factor_name,
            "score": self.score,
            "weight": self.weight,
            "explanation": self.explanation,
            "contributing_details": self.contributing_details
        }


class MissingDocumentationRiskFactor:
    """Calculates risk based on missing documentation"""
    
    MANDATORY_DOCUMENTS = {
        "discharge_summary": {"weight": 0.3, "denial_reason": "Missing discharge summary"},
        "operative_note": {"weight": 0.25, "denial_reason": "Missing operative note"},
        "itemized_bill": {"weight": 0.2, "denial_reason": "Missing itemized bill"},
        "insurance_card": {"weight": 0.15, "denial_reason": "Missing insurance card"},
        "identity_proof": {"weight": 0.1, "denial_reason": "Missing identity proof"}
    }
    
    @classmethod
    def calculate(cls, documents: List[Dict[str, Any]], validation_findings: List[Dict] = None) -> RiskFactorResult:
        """
        Calculate risk score based on missing documentation.
        
        Args:
            documents: List of uploaded documents
            validation_findings: Validation findings for additional context
            
        Returns:
            RiskFactorResult with score and explanation
        """
        present_types = {doc.get("document_type", "").lower() for doc in documents}
        
        missing_docs = []
        total_weight = 0.0
        missing_weight = 0.0
        
        for doc_type, info in cls.MANDATORY_DOCUMENTS.items():
            total_weight += info["weight"]
            if doc_type not in present_types:
                missing_docs.append(doc_type)
                missing_weight += info["weight"]
        
        # Calculate score (0 = all docs present, 1 = all docs missing)
        score = missing_weight / total_weight if total_weight > 0 else 0.0
        
        # Build explanation
        if score == 0:
            explanation = "All mandatory documents are present."
        elif score < 0.3:
            explanation = f"Minor documentation gaps: {', '.join(missing_docs)}. Low denial risk."
        elif score < 0.6:
            explanation = f"Significant documentation missing: {', '.join(missing_docs)}. Moderate denial risk."
        else:
            explanation = f"Critical documentation missing: {', '.join(missing_docs)}. High denial risk."
        
        # Build contributing details
        contributing_details = [
            {
                "document_type": doc_type,
                "is_present": doc_type in present_types,
                "weight": info["weight"],
                "denial_reason": info["denial_reason"]
            }
            for doc_type, info in cls.MANDATORY_DOCUMENTS.items()
        ]
        
        return RiskFactorResult(
            factor_name="missing_documentation",
            score=score,
            weight=0.25,  # 25% weight in overall prediction
            explanation=explanation,
            contributing_details=contributing_details
        )


class AuthorizationRiskFactor:
    """Calculates risk based on authorization status"""
    
    @classmethod
    def calculate(cls, clinical_data: Dict[str, Any], validation_findings: List[Dict] = None) -> RiskFactorResult:
        """
        Calculate risk score based on authorization status.
        
        Args:
            clinical_data: Normalized clinical data
            validation_findings: Validation findings for authorization issues
            
        Returns:
            RiskFactorResult with score and explanation
        """
        score = 0.0
        contributing_details = []
        
        # Check for authorization in validation findings
        auth_findings = []
        if validation_findings:
            auth_findings = [f for f in validation_findings if f.get("category") == "missing_authorization"]
        
        # Check claim amount for authorization requirement
        bill_amount = clinical_data.get("bill_amount")
        if bill_amount:
            try:
                amount = float(bill_amount)
                if amount > 50000:  # High-value claims require authorization
                    if auth_findings:
                        score = 0.9  # High risk if authorization missing for high-value claim
                        contributing_details.append({
                            "factor": "high_value_claim",
                            "amount": amount,
                            "authorization_required": True,
                            "authorization_present": False,
                            "impact": "High-value claims without pre-authorization are frequently denied"
                        })
                    else:
                        score = 0.1  # Low risk if authorization present
                        contributing_details.append({
                            "factor": "high_value_claim",
                            "amount": amount,
                            "authorization_required": True,
                            "authorization_present": True,
                            "impact": "Authorization present for high-value claim"
                        })
                else:
                    score = 0.2  # Low risk for standard claims
                    contributing_details.append({
                        "factor": "standard_claim",
                        "amount": amount,
                        "authorization_required": False,
                        "impact": "Standard claim, authorization not typically required"
                    })
            except (ValueError, TypeError):
                score = 0.5  # Medium risk if amount invalid
                contributing_details.append({
                    "factor": "invalid_amount",
                    "amount": bill_amount,
                    "impact": "Unable to determine authorization requirement due to invalid amount"
                })
        else:
            score = 0.3  # Low-medium risk if amount missing
            contributing_details.append({
                "factor": "missing_amount",
                "impact": "Unable to determine authorization requirement"
            })
        
        # Build explanation
        if score < 0.3:
            explanation = "Authorization requirements met or not applicable. Low denial risk."
        elif score < 0.6:
            explanation = "Authorization status unclear. Moderate denial risk."
        else:
            explanation = "Missing authorization for high-value claim. High denial risk."
        
        return RiskFactorResult(
            factor_name="authorization",
            score=score,
            weight=0.2,  # 20% weight in overall prediction
            explanation=explanation,
            contributing_details=contributing_details
        )


class CodingRiskFactor:
    """Calculates risk based on coding issues"""
    
    @classmethod
    def calculate(cls, coding_review_findings: List[Dict] = None, clinical_data: Dict[str, Any] = None) -> RiskFactorResult:
        """
        Calculate risk score based on coding review findings.
        
        Args:
            coding_review_findings: Coding review findings
            clinical_data: Clinical data for context
            
        Returns:
            RiskFactorResult with score and explanation
        """
        score = 0.0
        contributing_details = []
        
        if not coding_review_findings:
            # No coding review available - medium risk
            score = 0.4
            contributing_details.append({
                "factor": "no_coding_review",
                "impact": "Coding review not performed, unable to assess coding quality"
            })
        else:
            # Analyze coding findings
            critical_count = sum(1 for f in coding_review_findings if f.get("severity") == "critical")
            high_count = sum(1 for f in coding_review_findings if f.get("severity") == "high")
            medium_count = sum(1 for f in coding_review_findings if f.get("severity") == "medium")
            total_findings = len(coding_review_findings)
            
            # Calculate score based on severity
            if critical_count > 0:
                score = 0.95  # Very high risk with critical coding issues
                contributing_details.append({
                    "factor": "critical_coding_issues",
                    "count": critical_count,
                    "impact": "Critical coding issues (invalid codes, deleted codes) lead to automatic denial"
                })
            elif high_count > 0:
                score = 0.7  # High risk with high-severity issues
                contributing_details.append({
                    "factor": "high_severity_coding_issues",
                    "count": high_count,
                    "impact": "High-severity coding issues (bundling, medical necessity) increase denial risk"
                })
            elif medium_count > 0:
                score = 0.4  # Medium risk with medium-severity issues
                contributing_details.append({
                    "factor": "medium_severity_coding_issues",
                    "count": medium_count,
                    "impact": "Medium-severity coding issues may cause partial denial"
                })
            else:
                score = 0.1  # Low risk with no significant issues
                contributing_details.append({
                    "factor": "no_significant_issues",
                    "total_findings": total_findings,
                    "impact": "No significant coding issues detected"
                })
        
        # Build explanation
        if score < 0.3:
            explanation = "Coding review passed with no significant issues. Low denial risk."
        elif score < 0.6:
            explanation = "Coding review found medium-severity issues. Moderate denial risk."
        else:
            explanation = "Coding review found critical/high-severity issues. High denial risk."
        
        return RiskFactorResult(
            factor_name="coding",
            score=score,
            weight=0.25,  # 25% weight in overall prediction
            explanation=explanation,
            contributing_details=contributing_details
        )


class InsuranceRulesRiskFactor:
    """Calculates risk based on insurance-specific rules"""
    
    # Sample insurance-specific rules (in production, this would be comprehensive)
    INSURANCE_RULES = {
        "star_health": {
            "requires_tpa_approval_above": 50000,
            "cashless_only_for_network_hospitals": True,
            "pre_existing_disease_waiting_period": 36  # months
        },
        "apollo_munich": {
            "requires_tpa_approval_above": 30000,
            "cashless_only_for_network_hospitals": True,
            "pre_existing_disease_waiting_period": 48
        },
        "hdfc_ergo": {
            "requires_tpa_approval_above": 40000,
            "cashless_only_for_network_hospitals": True,
            "pre_existing_disease_waiting_period": 36
        },
        "icici_lombard": {
            "requires_tpa_approval_above": 35000,
            "cashless_only_for_network_hospitals": True,
            "pre_existing_disease_waiting_period": 48
        }
    }
    
    @classmethod
    def calculate(cls, clinical_data: Dict[str, Any], claim_data: Dict[str, Any] = None) -> RiskFactorResult:
        """
        Calculate risk score based on insurance-specific rules.
        
        Args:
            clinical_data: Normalized clinical data
            claim_data: Claim data including insurance information
            
        Returns:
            RiskFactorResult with score and explanation
        """
        score = 0.0
        contributing_details = []
        
        # Get insurance company
        insurance_company = clinical_data.get("insurance_company", "").lower()
        if not insurance_company:
            score = 0.5  # Medium risk if insurance unknown
            contributing_details.append({
                "factor": "unknown_insurance",
                "impact": "Unable to apply insurance-specific rules"
            })
        else:
            # Normalize insurance name
            insurance_key = None
            for key in cls.INSURANCE_RULES.keys():
                if key in insurance_company:
                    insurance_key = key
                    break
            
            if not insurance_key:
                score = 0.4  # Medium-low risk for unknown insurer
                contributing_details.append({
                    "factor": "unknown_insurer_rules",
                    "insurance_company": insurance_company,
                    "impact": "Insurance-specific rules not available"
                })
            else:
                rules = cls.INSURANCE_RULES[insurance_key]
                bill_amount = clinical_data.get("bill_amount")
                
                # Check TPA approval requirement
                if bill_amount:
                    try:
                        amount = float(bill_amount)
                        if amount > rules["requires_tpa_approval_above"]:
                            # Check if TPA approval is present (simplified check)
                            has_tpa = "tpa" in str(claim_data or {}).lower() or "authorization" in str(claim_data or {}).lower()
                            if not has_tpa:
                                score = 0.8  # High risk
                                contributing_details.append({
                                    "factor": "tpa_approval_required",
                                    "insurance": insurance_key,
                                    "amount": amount,
                                    "threshold": rules["requires_tpa_approval_above"],
                                    "tpa_present": False,
                                    "impact": f"{insurance_key.replace('_', ' ').title()} requires TPA approval for claims above ₹{rules['requires_tpa_approval_above']}"
                                })
                            else:
                                score = 0.2  # Low risk
                                contributing_details.append({
                                    "factor": "tpa_approval_present",
                                    "insurance": insurance_key,
                                    "amount": amount,
                                    "threshold": rules["requires_tpa_approval_above"],
                                    "tpa_present": True,
                                    "impact": "TPA approval present for high-value claim"
                                })
                        else:
                            score = 0.2  # Low risk
                            contributing_details.append({
                                "factor": "below_tpa_threshold",
                                "insurance": insurance_key,
                                "amount": amount,
                                "threshold": rules["requires_tpa_approval_above"],
                                "impact": "Claim below TPA approval threshold"
                            })
                    except (ValueError, TypeError):
                        score = 0.5
                        contributing_details.append({
                            "factor": "invalid_amount",
                            "impact": "Unable to check TPA requirement due to invalid amount"
                        })
                else:
                    score = 0.3
                    contributing_details.append({
                        "factor": "missing_amount",
                        "impact": "Unable to check TPA requirement"
                    })
        
        # Build explanation
        if score < 0.3:
            explanation = "Insurance-specific rules met. Low denial risk."
        elif score < 0.6:
            explanation = "Insurance-specific rules partially met. Moderate denial risk."
        else:
            explanation = "Insurance-specific rules not met. High denial risk."
        
        return RiskFactorResult(
            factor_name="insurance_rules",
            score=score,
            weight=0.15,  # 15% weight in overall prediction
            explanation=explanation,
            contributing_details=contributing_details
        )


class HistoricalPatternsRiskFactor:
    """Calculates risk based on historical denial patterns"""
    
    # Sample historical denial rates (in production, this would come from database)
    HISTORICAL_DENIAL_RATES = {
        "missing_documentation": 0.65,  # 65% denial rate
        "coding_errors": 0.55,
        "authorization_issues": 0.72,
        "insurance_rules": 0.48,
        "clinical_inconsistencies": 0.38
    }
    
    @classmethod
    def calculate(cls, hospital_id: str, patient_id: str = None, db = None) -> RiskFactorResult:
        """
        Calculate risk score based on historical patterns.
        
        Args:
            hospital_id: Hospital ID for historical data lookup
            patient_id: Patient ID for patient-specific history
            db: Database session for historical data
            
        Returns:
            RiskFactorResult with score and explanation
        """
        score = 0.0
        contributing_details = []
        
        # In production, this would query actual historical data
        # For now, we'll use a simplified approach
        
        # Simulate hospital-specific denial rate
        # In production: query historical claims for this hospital
        hospital_denial_rate = 0.25  # Placeholder - would be calculated from DB
        
        # Simulate patient-specific denial rate
        patient_denial_rate = 0.15  # Placeholder - would be calculated from DB
        
        # Combine rates
        combined_rate = (hospital_denial_rate * 0.7) + (patient_denial_rate * 0.3)
        score = combined_rate
        
        contributing_details.append({
            "factor": "hospital_denial_rate",
            "rate": hospital_denial_rate,
            "impact": f"Hospital has {hospital_denial_rate:.1%} historical denial rate"
        })
        
        if patient_id:
            contributing_details.append({
                "factor": "patient_denial_rate",
                "rate": patient_denial_rate,
                "impact": f"Patient has {patient_denial_rate:.1%} historical denial rate"
            })
        
        # Build explanation
        if score < 0.2:
            explanation = "Historical denial patterns favorable. Low denial risk."
        elif score < 0.4:
            explanation = "Historical denial patterns moderate. Medium denial risk."
        else:
            explanation = "Historical denial patterns unfavorable. High denial risk."
        
        return RiskFactorResult(
            factor_name="historical_patterns",
            score=score,
            weight=0.1,  # 10% weight in overall prediction
            explanation=explanation,
            contributing_details=contributing_details
        )


class ClinicalInconsistenciesRiskFactor:
    """Calculates risk based on clinical inconsistencies"""
    
    @classmethod
    def calculate(cls, clinical_data: Dict[str, Any], validation_findings: List[Dict] = None) -> RiskFactorResult:
        """
        Calculate risk score based on clinical inconsistencies.
        
        Args:
            clinical_data: Normalized clinical data
            validation_findings: Validation findings for clinical issues
            
        Returns:
            RiskFactorResult with score and explanation
        """
        score = 0.0
        contributing_details = []
        
        # Check validation findings for clinical inconsistencies
        inconsistency_findings = []
        if validation_findings:
            inconsistency_findings = [
                f for f in validation_findings 
                if f.get("category") in ["patient_mismatch", "date_inconsistency", "diagnosis_procedure_mismatch"]
            ]
        
        # Check for internal clinical inconsistencies
        internal_inconsistencies = []
        
        # Check date consistency
        admission_date = clinical_data.get("admission_date")
        discharge_date = clinical_data.get("discharge_date")
        operation_date = clinical_data.get("operation_date")
        
        if admission_date and discharge_date:
            try:
                from dateutil import parser
                adm = parser.parse(str(admission_date))
                dis = parser.parse(str(discharge_date))
                if adm > dis:
                    internal_inconsistencies.append({
                        "type": "date_inconsistency",
                        "issue": "Admission date after discharge date"
                    })
            except:
                pass
        
        # Check diagnosis-procedure alignment
        diagnosis = clinical_data.get("diagnosis")
        procedure = clinical_data.get("procedure")
        if diagnosis and not procedure:
            internal_inconsistencies.append({
                "type": "diagnosis_procedure_mismatch",
                "issue": "Diagnosis present but no procedure documented"
            })
        
        # Calculate score
        total_inconsistencies = len(inconsistency_findings) + len(internal_inconsistencies)
        
        if total_inconsistencies == 0:
            score = 0.1  # Low risk
            contributing_details.append({
                "factor": "no_inconsistencies",
                "impact": "No clinical inconsistencies detected"
            })
        elif total_inconsistencies <= 2:
            score = 0.4  # Medium risk
            contributing_details.append({
                "factor": "minor_inconsistencies",
                "count": total_inconsistencies,
                "impact": f"{total_inconsistencies} clinical inconsistency(ies) detected"
            })
        else:
            score = 0.8  # High risk
            contributing_details.append({
                "factor": "major_inconsistencies",
                "count": total_inconsistencies,
                "impact": f"{total_inconsistencies} clinical inconsistencies detected - high denial risk"
            })
        
        # Add validation findings to details
        if inconsistency_findings:
            contributing_details.extend([
                {
                    "factor": "validation_finding",
                    "category": f.get("category"),
                    "severity": f.get("severity"),
                    "explanation": f.get("explanation")
                }
                for f in inconsistency_findings
            ])
        
        # Add internal inconsistencies to details
        if internal_inconsistencies:
            contributing_details.extend([
                {
                    "factor": "internal_inconsistency",
                    "type": inc["type"],
                    "issue": inc["issue"]
                }
                for inc in internal_inconsistencies
            ])
        
        # Build explanation
        if score < 0.3:
            explanation = "No clinical inconsistencies detected. Low denial risk."
        elif score < 0.6:
            explanation = "Minor clinical inconsistencies detected. Moderate denial risk."
        else:
            explanation = "Major clinical inconsistencies detected. High denial risk."
        
        return RiskFactorResult(
            factor_name="clinical_inconsistencies",
            score=score,
            weight=0.05,  # 5% weight in overall prediction
            explanation=explanation,
            contributing_details=contributing_details
        )
