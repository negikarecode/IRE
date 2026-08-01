"""
Standardized AI Recommendation Structure

All AI recommendations must follow this structure for auditability and explainability.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel


class AIRecommendation(BaseModel):
    """Standardized AI recommendation structure"""
    
    issue: str  # Clear description of the issue detected
    evidence: str  # Specific evidence supporting the finding
    relevant_extracted_fields: Dict[str, Any]  # Fields from extracted data that led to this conclusion
    supporting_documents: List[str]  # Document IDs or names that contain the evidence
    reasoning: str  # Step-by-step explanation of how AI reached this conclusion
    recommended_action: str  # Specific action to address the issue
    confidence: float  # Confidence score (0.0 to 1.0)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "issue": self.issue,
            "evidence": self.evidence,
            "relevant_extracted_fields": self.relevant_extracted_fields,
            "supporting_documents": self.supporting_documents,
            "reasoning": self.reasoning,
            "recommended_action": self.recommended_action,
            "confidence": self.confidence
        }


class RecommendationBuilder:
    """Helper class to build standardized recommendations"""
    
    @staticmethod
    def build(
        issue: str,
        evidence: str,
        relevant_extracted_fields: Dict[str, Any],
        supporting_documents: List[str],
        reasoning: str,
        recommended_action: str,
        confidence: float
    ) -> AIRecommendation:
        """
        Build a standardized AI recommendation.
        
        Args:
            issue: Clear description of the issue
            evidence: Specific evidence supporting the finding
            relevant_extracted_fields: Fields from extracted data
            supporting_documents: Document IDs/names with evidence
            reasoning: Step-by-step explanation
            recommended_action: Specific action to address
            confidence: Confidence score (0.0 to 1.0)
            
        Returns:
            AIRecommendation object
        """
        return AIRecommendation(
            issue=issue,
            evidence=evidence,
            relevant_extracted_fields=relevant_extracted_fields,
            supporting_documents=supporting_documents,
            reasoning=reasoning,
            recommended_action=recommended_action,
            confidence=confidence
        )
    
    @staticmethod
    def from_validation_finding(finding: Dict[str, Any]) -> AIRecommendation:
        """Convert validation finding to standardized format"""
        return AIRecommendation(
            issue=finding.get("detected_issue", "Validation issue detected"),
            evidence=finding.get("evidence_text_snippet", "Evidence from document review"),
            relevant_extracted_fields={
                "affected_field": finding.get("affected_field"),
                "affected_document": finding.get("affected_document"),
                "severity": finding.get("severity"),
                "category": finding.get("category")
            },
            supporting_documents=[finding.get("affected_document", "Unknown")] if finding.get("affected_document") else [],
            reasoning=finding.get("explanation", "Based on validation rules"),
            recommended_action=finding.get("recommended_fix", "Review and correct the issue"),
            confidence=finding.get("confidence", 0.0)
        )
    
    @staticmethod
    def from_coding_finding(finding: Dict[str, Any]) -> AIRecommendation:
        """Convert coding review finding to standardized format"""
        return AIRecommendation(
            issue=finding.get("detected_issue", "Coding issue detected"),
            evidence=finding.get("evidence_text_snippet", "Evidence from clinical documentation"),
            relevant_extracted_fields={
                "code_type": finding.get("code_type"),
                "code_value": finding.get("code_value"),
                "modifier": finding.get("modifier"),
                "medical_evidence": finding.get("medical_evidence")
            },
            supporting_documents=[finding.get("reference_document", "Clinical Document")] if finding.get("reference_document") else [],
            reasoning=f"Based on coding guidelines: {finding.get('reference_document', 'Standard coding rules')}",
            recommended_action=finding.get("correct_coding_recommendation", "Review and correct the coding"),
            confidence=finding.get("confidence", 0.0)
        )
    
    @staticmethod
    def from_leakage_finding(finding: Dict[str, Any]) -> AIRecommendation:
        """Convert revenue leakage finding to standardized format"""
        return AIRecommendation(
            issue=finding.get("description", "Revenue leakage detected"),
            evidence=finding.get("source_text_snippet", "Evidence from document review"),
            relevant_extracted_fields={
                "category": finding.get("category"),
                "affected_code": finding.get("affected_code"),
                "supporting_evidence": finding.get("supporting_evidence")
            },
            supporting_documents=[finding.get("affected_document", "Unknown")] if finding.get("affected_document") else [],
            reasoning=f"Based on revenue analysis: {finding.get('category', 'Standard revenue rules')}",
            recommended_action=finding.get("recommended_correction", "Review and correct the charge"),
            confidence=finding.get("confidence", 0.0)
        )
    
    @staticmethod
    def from_denial_factor(factor: Dict[str, Any]) -> AIRecommendation:
        """Convert denial risk factor to standardized format"""
        details = factor.get("contributing_details", [])
        evidence = ", ".join([d.get("impact", "") for d in details[:2]]) if details else "Based on risk analysis"
        
        return AIRecommendation(
            issue=f"Denial risk factor: {factor.get('factor_name', 'Unknown')}",
            evidence=evidence,
            relevant_extracted_fields={
                "factor_name": factor.get("factor_name"),
                "score": factor.get("score"),
                "weight": factor.get("weight"),
                "contributing_details": details[:3]
            },
            supporting_documents=["Claim documents", "Clinical records"],
            reasoning=factor.get("explanation", "Based on historical patterns and rules"),
            recommended_action=f"Address {factor.get('factor_name', 'risk factor')} to reduce denial probability",
            confidence=1.0 - factor.get("score", 0.0)  # Higher confidence for lower risk
        )
