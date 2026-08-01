import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.infrastructure.db.models.claim import (
    CodingReviewFindingModel, CodingReviewSummaryModel,
    CodingReviewSeverity, CodingReviewCategory
)
from app.infrastructure.validators.coding_review_validators import (
    ICDCodeValidator,
    CPTCodeValidator,
    CodeCombinationValidator,
    DiagnosisProcedureCompatibilityValidator,
    BundlingValidator,
    MedicalNecessityValidator,
    CodingReviewFinding
)
from app.infrastructure.base.ai_recommendation import RecommendationBuilder

logger = logging.getLogger("coding_review_service")


class CodingReviewService:
    """Service for orchestrating medical coding review and storing findings"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def review_claim_coding(
        self,
        claim_id: str,
        hospital_id: str,
        clinical_data: Dict[str, Any],
        ocr_text: str = None,
        document_id: str = None
    ) -> Dict[str, Any]:
        """
        Perform comprehensive medical coding review.
        
        Args:
            claim_id: Claim ID for tracking
            hospital_id: Hospital ID for access control
            clinical_data: Normalized clinical data with codes
            ocr_text: OCR text for evidence search
            document_id: Source document ID for traceability
            
        Returns:
            dict with coding review results and summary
        """
        logger.info(f"[CODING_REVIEW_START] Claim ID: {claim_id}")
        
        all_findings = []
        
        # Extract codes from clinical data
        icd_codes = self._extract_codes(clinical_data.get("icd_codes", ""))
        cpt_codes = self._extract_codes(clinical_data.get("cpt_codes", ""))
        
        # 1. ICD Code Validation
        if icd_codes:
            icd_findings = ICDCodeValidator.validate(icd_codes, clinical_data, document_id)
            all_findings.extend(icd_findings)
        
        # 2. CPT Code Validation
        if cpt_codes:
            cpt_findings = CPTCodeValidator.validate(cpt_codes, clinical_data, document_id)
            all_findings.extend(cpt_findings)
        
        # 3. Code Combination Validation
        if cpt_codes:
            combination_findings = CodeCombinationValidator.validate(cpt_codes, clinical_data, document_id)
            all_findings.extend(combination_findings)
        
        # 4. Diagnosis-Procedure Compatibility Validation
        if icd_codes and cpt_codes:
            compatibility_findings = DiagnosisProcedureCompatibilityValidator.validate(
                icd_codes, cpt_codes, clinical_data, document_id
            )
            all_findings.extend(compatibility_findings)
        
        # 5. Bundling Validation
        if cpt_codes:
            bundling_findings = BundlingValidator.validate(cpt_codes, clinical_data, document_id)
            all_findings.extend(bundling_findings)
        
        # 6. Medical Necessity Validation
        if cpt_codes and icd_codes:
            necessity_findings = MedicalNecessityValidator.validate(
                cpt_codes, icd_codes, clinical_data, ocr_text, document_id
            )
            all_findings.extend(necessity_findings)
        
        # Store findings in database
        stored_findings = self._store_findings(
            all_findings,
            claim_id,
            hospital_id,
            document_id
        )
        
        # Create review summary
        summary = self._create_summary(
            claim_id,
            hospital_id,
            len(icd_codes),
            len(cpt_codes),
            all_findings
        )
        
        logger.info(f"[CODING_REVIEW_COMPLETE] Claim ID: {claim_id}, Total Findings: {len(all_findings)}")
        
        # Convert findings to standardized AI recommendation format
        standardized_findings = [
            RecommendationBuilder.from_coding_finding(finding.to_dict()).to_dict()
            for finding in all_findings
        ]
        
        return {
            "claim_id": claim_id,
            "hospital_id": hospital_id,
            "icd_codes_reviewed": len(icd_codes),
            "cpt_codes_reviewed": len(cpt_codes),
            "total_findings": len(all_findings),
            "findings": standardized_findings,
            "summary": summary,
            "can_submit": self._can_submit(summary)
        }
    
    def _extract_codes(self, codes_string: str) -> List[str]:
        """Extract codes from comma-separated string"""
        if not codes_string:
            return []
        
        if isinstance(codes_string, list):
            return codes_string
        
        return [code.strip() for code in str(codes_string).split(",") if code.strip()]
    
    def _store_findings(
        self,
        findings: List[CodingReviewFinding],
        claim_id: str,
        hospital_id: str,
        document_id: str = None
    ) -> List[CodingReviewFindingModel]:
        """Store coding review findings in database"""
        stored = []
        
        for finding in findings:
            try:
                finding_record = CodingReviewFindingModel(
                    id=str(__import__('uuid').uuid4()),
                    claim_id=claim_id,
                    hospital_id=hospital_id,
                    document_id=document_id,
                    code_type=finding.code_type,
                    code_value=finding.code_value,
                    modifier=finding.modifier,
                    severity=finding.severity,
                    category=finding.category,
                    confidence=finding.confidence,
                    detected_issue=finding.detected_issue,
                    correct_coding_recommendation=finding.correct_coding_recommendation,
                    reference_document=finding.reference_document,
                    expected_financial_impact=finding.expected_financial_impact,
                    medical_evidence=finding.medical_evidence,
                    evidence_source_document_id=finding.evidence_source_document_id,
                    evidence_text_snippet=finding.evidence_text_snippet,
                    evidence_page_number=finding.evidence_page_number,
                    review_timestamp=datetime.now(timezone.utc),
                    review_version="1.0"
                )
                self.db.add(finding_record)
                stored.append(finding_record)
            except Exception as e:
                logger.error(f"[FINDING_STORE_ERROR] {e}")
        
        self.db.commit()
        
        return stored
    
    def _create_summary(
        self,
        claim_id: str,
        hospital_id: str,
        icd_count: int,
        cpt_count: int,
        findings: List[CodingReviewFinding]
    ) -> Dict[str, Any]:
        """Create coding review summary"""
        # Count findings by severity
        critical = sum(1 for f in findings if f.severity == CodingReviewSeverity.CRITICAL.value)
        high = sum(1 for f in findings if f.severity == CodingReviewSeverity.HIGH.value)
        medium = sum(1 for f in findings if f.severity == CodingReviewSeverity.MEDIUM.value)
        low = sum(1 for f in findings if f.severity == CodingReviewSeverity.LOW.value)
        
        # Calculate total financial impact
        total_impact = sum(f.expected_financial_impact or 0 for f in findings)
        
        # Calculate overall confidence
        if findings:
            overall_confidence = sum(f.confidence for f in findings) / len(findings)
        else:
            overall_confidence = 1.0
        
        # Determine overall status
        if critical > 0:
            overall_status = "failed"
        elif high > 0:
            overall_status = "review_required"
        elif medium > 0:
            overall_status = "review_required"
        elif low > 0:
            overall_status = "passed_with_warnings"
        else:
            overall_status = "passed"
        
        # Store summary in database
        summary_record = CodingReviewSummaryModel(
            id=str(__import__('uuid').uuid4()),
            claim_id=claim_id,
            hospital_id=hospital_id,
            total_findings=len(findings),
            critical_findings=critical,
            high_findings=high,
            medium_findings=medium,
            low_findings=low,
            icd_codes_reviewed=icd_count,
            cpt_codes_reviewed=cpt_count,
            total_financial_impact=total_impact,
            impact_currency="INR",
            overall_status=overall_status,
            overall_confidence=overall_confidence,
            reviewed_at=datetime.now(timezone.utc),
            review_version="1.0"
        )
        
        # Update existing summary or create new
        existing = self.db.query(CodingReviewSummaryModel).filter(
            CodingReviewSummaryModel.claim_id == claim_id
        ).first()
        
        if existing:
            existing.total_findings = len(findings)
            existing.critical_findings = critical
            existing.high_findings = high
            existing.medium_findings = medium
            existing.low_findings = low
            existing.icd_codes_reviewed = icd_count
            existing.cpt_codes_reviewed = cpt_count
            existing.total_financial_impact = total_impact
            existing.overall_status = overall_status
            existing.overall_confidence = overall_confidence
            existing.reviewed_at = datetime.now(timezone.utc)
            existing.updated_at = datetime.now(timezone.utc)
        else:
            self.db.add(summary_record)
        
        self.db.commit()
        
        return {
            "total_findings": len(findings),
            "critical_findings": critical,
            "high_findings": high,
            "medium_findings": medium,
            "low_findings": low,
            "icd_codes_reviewed": icd_count,
            "cpt_codes_reviewed": cpt_count,
            "total_financial_impact": total_impact,
            "impact_currency": "INR",
            "overall_status": overall_status,
            "overall_confidence": overall_confidence
        }
    
    def _can_submit(self, summary: Dict[str, Any]) -> bool:
        """Determine if claim can be submitted based on coding review"""
        # Cannot submit if there are critical findings
        if summary.get("critical_findings", 0) > 0:
            return False
        
        # Cannot submit if there are high findings
        if summary.get("high_findings", 0) > 0:
            return False
        
        return True
    
    def get_findings_for_claim(
        self,
        claim_id: str,
        hospital_id: str,
        code_type: Optional[str] = None,
        severity: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[CodingReviewFindingModel]:
        """
        Get coding review findings for a claim.
        
        Args:
            claim_id: Claim ID
            hospital_id: Hospital ID for access control
            code_type: Optional code type filter (ICD, CPT, HCPCS)
            severity: Optional severity filter
            status: Optional status filter
            
        Returns:
            List of coding review findings
        """
        query = self.db.query(CodingReviewFindingModel).filter(
            CodingReviewFindingModel.claim_id == claim_id,
            CodingReviewFindingModel.hospital_id == hospital_id
        )
        
        if code_type:
            query = query.filter(CodingReviewFindingModel.code_type == code_type)
        
        if severity:
            query = query.filter(CodingReviewFindingModel.severity == severity)
        
        if status:
            query = query.filter(CodingReviewFindingModel.status == status)
        
        return query.all()
    
    def get_summary_for_claim(
        self,
        claim_id: str,
        hospital_id: str
    ) -> Optional[CodingReviewSummaryModel]:
        """
        Get coding review summary for a claim.
        
        Args:
            claim_id: Claim ID
            hospital_id: Hospital ID for access control
            
        Returns:
            Coding review summary or None
        """
        return self.db.query(CodingReviewSummaryModel).filter(
            CodingReviewSummaryModel.claim_id == claim_id,
            CodingReviewSummaryModel.hospital_id == hospital_id
        ).first()
    
    def acknowledge_finding(
        self,
        finding_id: str,
        user_id: str,
        hospital_id: str
    ) -> Optional[CodingReviewFindingModel]:
        """
        Acknowledge a coding review finding.
        
        Args:
            finding_id: Finding ID
            user_id: User ID acknowledging the finding
            hospital_id: Hospital ID for access control
            
        Returns:
            Updated finding or None
        """
        finding = self.db.query(CodingReviewFindingModel).filter(
            CodingReviewFindingModel.id == finding_id,
            CodingReviewFindingModel.hospital_id == hospital_id
        ).first()
        
        if not finding:
            return None
        
        finding.status = "acknowledged"
        finding.acknowledged_by = user_id
        finding.acknowledged_at = datetime.now(timezone.utc)
        finding.updated_at = datetime.now(timezone.utc)
        
        self.db.commit()
        self.db.refresh(finding)
        
        logger.info(f"[CODING_FINDING_ACKNOWLEDGED] ID: {finding_id}, User: {user_id}")
        
        return finding
    
    def mark_finding_fixed(
        self,
        finding_id: str,
        user_id: str,
        hospital_id: str
    ) -> Optional[CodingReviewFindingModel]:
        """
        Mark a coding review finding as fixed.
        
        Args:
            finding_id: Finding ID
            user_id: User ID marking as fixed
            hospital_id: Hospital ID for access control
            
        Returns:
            Updated finding or None
        """
        finding = self.db.query(CodingReviewFindingModel).filter(
            CodingReviewFindingModel.id == finding_id,
            CodingReviewFindingModel.hospital_id == hospital_id
        ).first()
        
        if not finding:
            return None
        
        finding.status = "fixed"
        finding.fixed_by = user_id
        finding.fixed_at = datetime.now(timezone.utc)
        finding.updated_at = datetime.now(timezone.utc)
        
        self.db.commit()
        self.db.refresh(finding)
        
        logger.info(f"[CODING_FINDING_FIXED] ID: {finding_id}, User: {user_id}")
        
        return finding
    
    def dismiss_finding(
        self,
        finding_id: str,
        user_id: str,
        hospital_id: str,
        reason: Optional[str] = None
    ) -> Optional[CodingReviewFindingModel]:
        """
        Dismiss a coding review finding with optional reason.
        
        Args:
            finding_id: Finding ID
            user_id: User ID dismissing the finding
            hospital_id: Hospital ID for access control
            reason: Reason for dismissal
            
        Returns:
            Updated finding or None
        """
        finding = self.db.query(CodingReviewFindingModel).filter(
            CodingReviewFindingModel.id == finding_id,
            CodingReviewFindingModel.hospital_id == hospital_id
        ).first()
        
        if not finding:
            return None
        
        finding.status = "dismissed"
        finding.acknowledged_by = user_id
        finding.acknowledged_at = datetime.now(timezone.utc)
        finding.updated_at = datetime.now(timezone.utc)
        
        if reason:
            finding.detected_issue = f"{finding.detected_issue} [Dismissed: {reason}]"
        
        self.db.commit()
        self.db.refresh(finding)
        
        logger.info(f"[CODING_FINDING_DISMISSED] ID: {finding_id}, User: {user_id}, Reason: {reason}")
        
        return finding
    
    def re_review_claim(
        self,
        claim_id: str,
        hospital_id: str,
        clinical_data: Dict[str, Any],
        ocr_text: str = None,
        document_id: str = None
    ) -> Dict[str, Any]:
        """
        Re-review a claim (clears old findings and creates new ones).
        
        Args:
            claim_id: Claim ID
            hospital_id: Hospital ID
            clinical_data: Clinical data with codes
            ocr_text: OCR text for evidence
            document_id: Source document ID
            
        Returns:
            dict with new coding review results
        """
        # Delete old findings
        self.db.query(CodingReviewFindingModel).filter(
            CodingReviewFindingModel.claim_id == claim_id,
            CodingReviewFindingModel.hospital_id == hospital_id
        ).delete()
        
        self.db.commit()
        
        logger.info(f"[CODING_RE_REVIEW] Cleared old findings for Claim ID: {claim_id}")
        
        # Run review again
        return self.review_claim_coding(
            claim_id,
            hospital_id,
            clinical_data,
            ocr_text,
            document_id
        )


def get_coding_review_service(db: Session) -> CodingReviewService:
    """Factory function to get coding review service instance"""
    return CodingReviewService(db)
