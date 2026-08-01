import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.infrastructure.db.models.claim import (
    RevenueLeakageFindingModel, RevenueLeakageSummaryModel,
    RevenueLeakageCategory
)
from app.infrastructure.detectors.revenue_leakage_detectors import (
    UnderbillingDetector,
    MissingProcedureDetector,
    MissingModifierDetector,
    MissedDiagnosisDetector,
    MissingImplantDetector,
    IncompleteChargesDetector,
    IncorrectCodingDetector,
    LeakageFinding
)
from app.infrastructure.base.ai_recommendation import RecommendationBuilder

logger = logging.getLogger("revenue_leakage_service")


class RevenueLeakageService:
    """Service for detecting revenue leakage in claims"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def detect_revenue_leakage(
        self,
        claim_id: str,
        hospital_id: str,
        clinical_data: Dict[str, Any],
        claim_amount: Any = None,
        ocr_text: str = None,
        document_id: str = None
    ) -> Dict[str, Any]:
        """
        Detect revenue leakage in a claim.
        
        Args:
            claim_id: Claim ID for tracking
            hospital_id: Hospital ID for access control
            clinical_data: Normalized clinical data
            claim_amount: Claim amount for comparison
            ocr_text: OCR text for evidence search
            document_id: Source document ID for traceability
            
        Returns:
            dict with revenue leakage detection results
        """
        logger.info(f"[REVENUE_LEAKAGE_DETECTION_START] Claim ID: {claim_id}")
        
        all_findings = []
        
        # 1. Underbilling Detection
        underbilling_findings = UnderbillingDetector.detect(clinical_data, claim_amount, document_id)
        all_findings.extend(underbilling_findings)
        
        # 2. Missing Procedure Detection
        missing_procedure_findings = MissingProcedureDetector.detect(clinical_data, ocr_text, document_id)
        all_findings.extend(missing_procedure_findings)
        
        # 3. Missing Modifier Detection
        missing_modifier_findings = MissingModifierDetector.detect(clinical_data, ocr_text, document_id)
        all_findings.extend(missing_modifier_findings)
        
        # 4. Missed Diagnosis Detection
        missed_diagnosis_findings = MissedDiagnosisDetector.detect(clinical_data, ocr_text, document_id)
        all_findings.extend(missed_diagnosis_findings)
        
        # 5. Missing Implant Detection
        missing_implant_findings = MissingImplantDetector.detect(clinical_data, ocr_text, document_id)
        all_findings.extend(missing_implant_findings)
        
        # 6. Incomplete Charges Detection
        incomplete_charges_findings = IncompleteChargesDetector.detect(clinical_data, claim_amount, document_id)
        all_findings.extend(incomplete_charges_findings)
        
        # 7. Incorrect Coding Detection
        incorrect_coding_findings = IncorrectCodingDetector.detect(clinical_data, ocr_text, document_id)
        all_findings.extend(incorrect_coding_findings)
        
        # Store findings in database
        stored_findings = self._store_findings(
            all_findings,
            claim_id,
            hospital_id,
            document_id
        )
        
        # Create summary
        summary = self._create_summary(
            claim_id,
            hospital_id,
            all_findings
        )
        
        logger.info(f"[REVENUE_LEAKAGE_DETECTION_COMPLETE] Claim ID: {claim_id}, Total Findings: {len(all_findings)}, Recoverable: ₹{summary.get('total_recoverable_revenue', 0):.2f}")
        
        # Convert findings to standardized AI recommendation format
        standardized_findings = [
            RecommendationBuilder.from_leakage_finding(finding.to_dict()).to_dict()
            for finding in all_findings
        ]
        
        return {
            "claim_id": claim_id,
            "hospital_id": hospital_id,
            "total_findings": len(all_findings),
            "findings": standardized_findings,
            "summary": summary
        }
    
    def _store_findings(
        self,
        findings: List[LeakageFinding],
        claim_id: str,
        hospital_id: str,
        document_id: str = None
    ) -> List[RevenueLeakageFindingModel]:
        """Store revenue leakage findings in database"""
        stored = []
        
        for finding in findings:
            try:
                finding_record = RevenueLeakageFindingModel(
                    id=str(__import__('uuid').uuid4()),
                    claim_id=claim_id,
                    hospital_id=hospital_id,
                    document_id=document_id,
                    category=finding.category,
                    confidence=finding.confidence,
                    estimated_recoverable_revenue=finding.estimated_recoverable_revenue,
                    revenue_currency="INR",
                    description=finding.description,
                    recommended_correction=finding.recommended_correction,
                    supporting_evidence=finding.supporting_evidence,
                    affected_document=finding.affected_document,
                    affected_code=finding.affected_code,
                    source_document_id=finding.source_document_id,
                    source_text_snippet=finding.source_text_snippet,
                    detection_timestamp=datetime.now(timezone.utc),
                    detection_model_version="1.0"
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
        findings: List[LeakageFinding]
    ) -> Dict[str, Any]:
        """Create revenue leakage summary"""
        # Count findings by category
        category_counts = {
            RevenueLeakageCategory.UNDERBILLING.value: 0,
            RevenueLeakageCategory.MISSING_PROCEDURE.value: 0,
            RevenueLeakageCategory.MISSING_MODIFIER.value: 0,
            RevenueLeakageCategory.MISSED_DIAGNOSIS.value: 0,
            RevenueLeakageCategory.MISSING_IMPLANT.value: 0,
            RevenueLeakageCategory.INCOMPLETE_CHARGES.value: 0,
            RevenueLeakageCategory.INCORRECT_CODING.value: 0
        }
        
        total_recoverable = 0.0
        
        for finding in findings:
            if finding.category in category_counts:
                category_counts[finding.category] += 1
            if finding.estimated_recoverable_revenue:
                total_recoverable += finding.estimated_recoverable_revenue
        
        # Store summary in database
        summary_record = RevenueLeakageSummaryModel(
            id=str(__import__('uuid').uuid4()),
            claim_id=claim_id,
            hospital_id=hospital_id,
            total_findings=len(findings),
            total_recoverable_revenue=total_recoverable,
            revenue_currency="INR",
            underbilling_count=category_counts[RevenueLeakageCategory.UNDERBILLING.value],
            missing_procedure_count=category_counts[RevenueLeakageCategory.MISSING_PROCEDURE.value],
            missing_modifier_count=category_counts[RevenueLeakageCategory.MISSING_MODIFIER.value],
            missed_diagnosis_count=category_counts[RevenueLeakageCategory.MISSED_DIAGNOSIS.value],
            missing_implant_count=category_counts[RevenueLeakageCategory.MISSING_IMPLANT.value],
            incomplete_charges_count=category_counts[RevenueLeakageCategory.INCOMPLETE_CHARGES.value],
            incorrect_coding_count=category_counts[RevenueLeakageCategory.INCORRECT_CODING.value],
            recovered_amount=0.0,
            detection_timestamp=datetime.now(timezone.utc),
            detection_model_version="1.0"
        )
        
        # Update existing summary or create new
        existing = self.db.query(RevenueLeakageSummaryModel).filter(
            RevenueLeakageSummaryModel.claim_id == claim_id
        ).first()
        
        if existing:
            existing.total_findings = len(findings)
            existing.total_recoverable_revenue = total_recoverable
            existing.underbilling_count = category_counts[RevenueLeakageCategory.UNDERBILLING.value]
            existing.missing_procedure_count = category_counts[RevenueLeakageCategory.MISSING_PROCEDURE.value]
            existing.missing_modifier_count = category_counts[RevenueLeakageCategory.MISSING_MODIFIER.value]
            existing.missed_diagnosis_count = category_counts[RevenueLeakageCategory.MISSED_DIAGNOSIS.value]
            existing.missing_implant_count = category_counts[RevenueLeakageCategory.MISSING_IMPLANT.value]
            existing.incomplete_charges_count = category_counts[RevenueLeakageCategory.INCOMPLETE_CHARGES.value]
            existing.incorrect_coding_count = category_counts[RevenueLeakageCategory.INCORRECT_CODING.value]
            existing.detection_timestamp = datetime.now(timezone.utc)
            existing.updated_at = datetime.now(timezone.utc)
        else:
            self.db.add(summary_record)
        
        self.db.commit()
        
        return {
            "total_findings": len(findings),
            "total_recoverable_revenue": total_recoverable,
            "revenue_currency": "INR",
            "category_breakdown": category_counts
        }
    
    def get_findings_for_claim(
        self,
        claim_id: str,
        hospital_id: str,
        category: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[RevenueLeakageFindingModel]:
        """
        Get revenue leakage findings for a claim.
        
        Args:
            claim_id: Claim ID
            hospital_id: Hospital ID for access control
            category: Optional category filter
            status: Optional status filter
            
        Returns:
            List of revenue leakage findings
        """
        query = self.db.query(RevenueLeakageFindingModel).filter(
            RevenueLeakageFindingModel.claim_id == claim_id,
            RevenueLeakageFindingModel.hospital_id == hospital_id
        )
        
        if category:
            query = query.filter(RevenueLeakageFindingModel.category == category)
        
        if status:
            query = query.filter(RevenueLeakageFindingModel.status == status)
        
        return query.all()
    
    def get_summary_for_claim(
        self,
        claim_id: str,
        hospital_id: str
    ) -> Optional[RevenueLeakageSummaryModel]:
        """
        Get revenue leakage summary for a claim.
        
        Args:
            claim_id: Claim ID
            hospital_id: Hospital ID for access control
            
        Returns:
            Revenue leakage summary or None
        """
        return self.db.query(RevenueLeakageSummaryModel).filter(
            RevenueLeakageSummaryModel.claim_id == claim_id,
            RevenueLeakageSummaryModel.hospital_id == hospital_id
        ).first()
    
    def acknowledge_finding(
        self,
        finding_id: str,
        user_id: str,
        hospital_id: str
    ) -> Optional[RevenueLeakageFindingModel]:
        """
        Acknowledge a revenue leakage finding.
        
        Args:
            finding_id: Finding ID
            user_id: User ID acknowledging the finding
            hospital_id: Hospital ID for access control
            
        Returns:
            Updated finding or None
        """
        finding = self.db.query(RevenueLeakageFindingModel).filter(
            RevenueLeakageFindingModel.id == finding_id,
            RevenueLeakageFindingModel.hospital_id == hospital_id
        ).first()
        
        if not finding:
            return None
        
        finding.status = "acknowledged"
        finding.acknowledged_by = user_id
        finding.acknowledged_at = datetime.now(timezone.utc)
        finding.updated_at = datetime.now(timezone.utc)
        
        self.db.commit()
        self.db.refresh(finding)
        
        logger.info(f"[LEAKAGE_FINDING_ACKNOWLEDGED] ID: {finding_id}, User: {user_id}")
        
        return finding
    
    def mark_finding_recovered(
        self,
        finding_id: str,
        user_id: str,
        hospital_id: str,
        recovered_amount: float = None
    ) -> Optional[RevenueLeakageFindingModel]:
        """
        Mark a revenue leakage finding as recovered.
        
        Args:
            finding_id: Finding ID
            user_id: User ID marking as recovered
            hospital_id: Hospital ID for access control
            recovered_amount: Actual amount recovered
            
        Returns:
            Updated finding or None
        """
        finding = self.db.query(RevenueLeakageFindingModel).filter(
            RevenueLeakageFindingModel.id == finding_id,
            RevenueLeakageFindingModel.hospital_id == hospital_id
        ).first()
        
        if not finding:
            return None
        
        finding.status = "recovered"
        finding.recovered_by = user_id
        finding.recovered_at = datetime.now(timezone.utc)
        finding.recovered_amount = recovered_amount or finding.estimated_recoverable_revenue
        finding.updated_at = datetime.now(timezone.utc)
        
        # Update summary
        summary = self.db.query(RevenueLeakageSummaryModel).filter(
            RevenueLeakageSummaryModel.claim_id == finding.claim_id
        ).first()
        if summary:
            summary.recovered_amount = (summary.recovered_amount or 0) + finding.recovered_amount
            if summary.total_recoverable_revenue and summary.total_recoverable_revenue > 0:
                summary.recovery_percentage = (summary.recovered_amount / summary.total_recoverable_revenue) * 100
            summary.updated_at = datetime.now(timezone.utc)
        
        self.db.commit()
        self.db.refresh(finding)
        
        logger.info(f"[LEAKAGE_FINDING_RECOVERED] ID: {finding_id}, User: {user_id}, Amount: ₹{finding.recovered_amount}")
        
        return finding
    
    def dismiss_finding(
        self,
        finding_id: str,
        user_id: str,
        hospital_id: str,
        reason: Optional[str] = None
    ) -> Optional[RevenueLeakageFindingModel]:
        """
        Dismiss a revenue leakage finding with optional reason.
        
        Args:
            finding_id: Finding ID
            user_id: User ID dismissing the finding
            hospital_id: Hospital ID for access control
            reason: Reason for dismissal
            
        Returns:
            Updated finding or None
        """
        finding = self.db.query(RevenueLeakageFindingModel).filter(
            RevenueLeakageFindingModel.id == finding_id,
            RevenueLeakageFindingModel.hospital_id == hospital_id
        ).first()
        
        if not finding:
            return None
        
        finding.status = "dismissed"
        finding.acknowledged_by = user_id
        finding.acknowledged_at = datetime.now(timezone.utc)
        finding.updated_at = datetime.now(timezone.utc)
        
        if reason:
            finding.description = f"{finding.description} [Dismissed: {reason}]"
        
        self.db.commit()
        self.db.refresh(finding)
        
        logger.info(f"[LEAKAGE_FINDING_DISMISSED] ID: {finding_id}, User: {user_id}, Reason: {reason}")
        
        return finding
    
    def re_detect(
        self,
        claim_id: str,
        hospital_id: str,
        clinical_data: Dict[str, Any],
        claim_amount: Any = None,
        ocr_text: str = None,
        document_id: str = None
    ) -> Dict[str, Any]:
        """
        Re-detect revenue leakage (clears old findings and creates new ones).
        
        Args:
            claim_id: Claim ID
            hospital_id: Hospital ID
            clinical_data: Clinical data
            claim_amount: Claim amount
            ocr_text: OCR text
            document_id: Source document ID
            
        Returns:
            dict with new detection results
        """
        # Delete old findings
        self.db.query(RevenueLeakageFindingModel).filter(
            RevenueLeakageFindingModel.claim_id == claim_id,
            RevenueLeakageFindingModel.hospital_id == hospital_id
        ).delete()
        
        self.db.commit()
        
        logger.info(f"[REVENUE_LEAKAGE_RE_DETECT] Cleared old findings for Claim ID: {claim_id}")
        
        # Run detection again
        return self.detect_revenue_leakage(
            claim_id,
            hospital_id,
            clinical_data,
            claim_amount,
            ocr_text,
            document_id
        )


def get_revenue_leakage_service(db: Session) -> RevenueLeakageService:
    """Factory function to get revenue leakage service instance"""
    return RevenueLeakageService(db)
