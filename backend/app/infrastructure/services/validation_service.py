import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.infrastructure.db.models.claim import (
    ValidationFindingModel, ValidationSummaryModel,
    ValidationSeverity, ValidationCategory
)
from app.infrastructure.validators.claim_validators import (
    MissingDocumentValidator,
    MissingDiagnosisValidator,
    MissingSignatureValidator,
    MissingAuthorizationValidator,
    CodingInconsistencyValidator,
    PatientMismatchValidator,
    DateInconsistencyValidator,
    DuplicateBillingValidator,
    DocumentCompletenessValidator,
    MissingCredentialsValidator,
    MissingIdentifiersValidator,
    ValidationFinding
)
from app.infrastructure.base.ai_recommendation import RecommendationBuilder

logger = logging.getLogger("validation_service")


class ClaimValidationService:
    """Service for orchestrating claim validation and storing findings"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def validate_claim(
        self,
        claim_id: str,
        hospital_id: str,
        documents: List[Dict[str, Any]],
        clinical_data_list: List[Dict[str, Any]],
        claim_data: Dict[str, Any],
        ocr_texts: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """
        Perform comprehensive claim validation.
        
        Args:
            claim_id: Claim ID for tracking
            hospital_id: Hospital ID for access control
            documents: List of uploaded documents with metadata
            clinical_data_list: List of clinical extraction data from documents
            claim_data: Master claim data
            ocr_texts: Dictionary mapping document_id to OCR text
            
        Returns:
            dict with validation results and summary
        """
        logger.info(f"[CLAIM_VALIDATION_START] Claim ID: {claim_id}")
        
        all_findings = []
        
        # Initialize OCR texts if not provided
        if ocr_texts is None:
            ocr_texts = {}
        
        # 1. Missing Document Validation
        missing_doc_findings = MissingDocumentValidator.validate(documents, claim_data)
        all_findings.extend(missing_doc_findings)
        
        # 2. Validate each document's clinical data
        for i, clinical_data in enumerate(clinical_data_list):
            document_id = clinical_data.get("document_id")
            document_type = clinical_data.get("document_type", "unknown")
            ocr_text = ocr_texts.get(document_id, "")
            
            # Missing Diagnosis Validation
            diagnosis_findings = MissingDiagnosisValidator.validate(clinical_data, document_id)
            all_findings.extend(diagnosis_findings)
            
            # Missing Signature Validation
            signature_findings = MissingSignatureValidator.validate(ocr_text, document_id, document_type)
            all_findings.extend(signature_findings)
            
            # Missing Authorization Validation
            auth_findings = MissingAuthorizationValidator.validate(clinical_data, ocr_text, document_id)
            all_findings.extend(auth_findings)
            
            # Coding Inconsistency Validation
            coding_findings = CodingInconsistencyValidator.validate(clinical_data, document_id)
            all_findings.extend(coding_findings)
            
            # Date Inconsistency Validation
            date_findings = DateInconsistencyValidator.validate(clinical_data, document_id)
            all_findings.extend(date_findings)
            
            # Duplicate Billing Validation
            duplicate_findings = DuplicateBillingValidator.validate(clinical_data, ocr_text, document_id)
            all_findings.extend(duplicate_findings)
            
            # Document Completeness Validation
            completeness_findings = DocumentCompletenessValidator.validate(ocr_text, document_type, document_id)
            all_findings.extend(completeness_findings)
            
            # Missing Credentials Validation
            credentials_findings = MissingCredentialsValidator.validate(clinical_data, ocr_text, document_id)
            all_findings.extend(credentials_findings)
            
            # Missing Identifiers Validation
            identifiers_findings = MissingIdentifiersValidator.validate(clinical_data, document_id)
            all_findings.extend(identifiers_findings)
        
        # 3. Patient Mismatch Validation (across all documents)
        patient_findings = PatientMismatchValidator.validate(clinical_data_list, claim_data)
        all_findings.extend(patient_findings)
        
        # Store findings in database
        stored_findings = self._store_findings(
            all_findings,
            claim_id,
            hospital_id
        )
        
        # Create validation summary
        summary = self._create_summary(
            claim_id,
            hospital_id,
            all_findings
        )
        
        logger.info(f"[CLAIM_VALIDATION_COMPLETE] Claim ID: {claim_id}, Total Findings: {len(all_findings)}")
        
        # Convert findings to standardized AI recommendation format
        standardized_findings = [
            RecommendationBuilder.from_validation_finding(finding.to_dict()).to_dict()
            for finding in all_findings
        ]
        
        return {
            "claim_id": claim_id,
            "hospital_id": hospital_id,
            "total_findings": len(all_findings),
            "findings": standardized_findings,
            "summary": summary,
            "can_submit": self._can_submit(summary)
        }
    
    def _store_findings(
        self,
        findings: List[ValidationFinding],
        claim_id: str,
        hospital_id: str
    ) -> List[ValidationFindingModel]:
        """Store validation findings in database"""
        stored = []
        
        for finding in findings:
            try:
                finding_record = ValidationFindingModel(
                    id=str(__import__('uuid').uuid4()),
                    claim_id=claim_id,
                    hospital_id=hospital_id,
                    document_id=finding.source_document_id,
                    severity=finding.severity,
                    category=finding.category,
                    confidence=finding.confidence,
                    affected_document=finding.affected_document,
                    affected_field=finding.affected_field,
                    explanation=finding.explanation,
                    recommended_fix=finding.recommended_fix,
                    source_document_id=finding.source_document_id,
                    source_page_number=finding.source_page_number,
                    source_text_snippet=finding.source_text_snippet,
                    validation_timestamp=datetime.now(timezone.utc)
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
        findings: List[ValidationFinding]
    ) -> Dict[str, Any]:
        """Create validation summary"""
        # Count findings by severity
        critical = sum(1 for f in findings if f.severity == ValidationSeverity.CRITICAL.value)
        high = sum(1 for f in findings if f.severity == ValidationSeverity.HIGH.value)
        medium = sum(1 for f in findings if f.severity == ValidationSeverity.MEDIUM.value)
        low = sum(1 for f in findings if f.severity == ValidationSeverity.LOW.value)
        info = sum(1 for f in findings if f.severity == ValidationSeverity.INFO.value)
        
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
        elif low > 0 or info > 0:
            overall_status = "passed_with_warnings"
        else:
            overall_status = "passed"
        
        # Store summary in database
        summary_record = ValidationSummaryModel(
            id=str(__import__('uuid').uuid4()),
            claim_id=claim_id,
            hospital_id=hospital_id,
            total_findings=len(findings),
            critical_findings=critical,
            high_findings=high,
            medium_findings=medium,
            low_findings=low,
            overall_status=overall_status,
            overall_confidence=overall_confidence,
            validated_at=datetime.now(timezone.utc),
            validation_version="1.0"
        )
        
        # Update existing summary or create new
        existing = self.db.query(ValidationSummaryModel).filter(
            ValidationSummaryModel.claim_id == claim_id
        ).first()
        
        if existing:
            existing.total_findings = len(findings)
            existing.critical_findings = critical
            existing.high_findings = high
            existing.medium_findings = medium
            existing.low_findings = low
            existing.overall_status = overall_status
            existing.overall_confidence = overall_confidence
            existing.validated_at = datetime.now(timezone.utc)
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
            "info_findings": info,
            "overall_status": overall_status,
            "overall_confidence": overall_confidence
        }
    
    def _can_submit(self, summary: Dict[str, Any]) -> bool:
        """Determine if claim can be submitted based on validation"""
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
        severity: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[ValidationFindingModel]:
        """
        Get validation findings for a claim.
        
        Args:
            claim_id: Claim ID
            hospital_id: Hospital ID for access control
            severity: Optional severity filter
            status: Optional status filter
            
        Returns:
            List of validation findings
        """
        query = self.db.query(ValidationFindingModel).filter(
            ValidationFindingModel.claim_id == claim_id,
            ValidationFindingModel.hospital_id == hospital_id
        )
        
        if severity:
            query = query.filter(ValidationFindingModel.severity == severity)
        
        if status:
            query = query.filter(ValidationFindingModel.status == status)
        
        return query.all()
    
    def get_summary_for_claim(
        self,
        claim_id: str,
        hospital_id: str
    ) -> Optional[ValidationSummaryModel]:
        """
        Get validation summary for a claim.
        
        Args:
            claim_id: Claim ID
            hospital_id: Hospital ID for access control
            
        Returns:
            Validation summary or None
        """
        return self.db.query(ValidationSummaryModel).filter(
            ValidationSummaryModel.claim_id == claim_id,
            ValidationSummaryModel.hospital_id == hospital_id
        ).first()
    
    def acknowledge_finding(
        self,
        finding_id: str,
        user_id: str,
        hospital_id: str
    ) -> Optional[ValidationFindingModel]:
        """
        Acknowledge a validation finding.
        
        Args:
            finding_id: Finding ID
            user_id: User ID acknowledging the finding
            hospital_id: Hospital ID for access control
            
        Returns:
            Updated finding or None
        """
        finding = self.db.query(ValidationFindingModel).filter(
            ValidationFindingModel.id == finding_id,
            ValidationFindingModel.hospital_id == hospital_id
        ).first()
        
        if not finding:
            return None
        
        finding.status = "acknowledged"
        finding.acknowledged_by = user_id
        finding.acknowledged_at = datetime.now(timezone.utc)
        finding.updated_at = datetime.now(timezone.utc)
        
        self.db.commit()
        self.db.refresh(finding)
        
        logger.info(f"[FINDING_ACKNOWLEDGED] ID: {finding_id}, User: {user_id}")
        
        return finding
    
    def mark_finding_fixed(
        self,
        finding_id: str,
        user_id: str,
        hospital_id: str
    ) -> Optional[ValidationFindingModel]:
        """
        Mark a validation finding as fixed.
        
        Args:
            finding_id: Finding ID
            user_id: User ID marking as fixed
            hospital_id: Hospital ID for access control
            
        Returns:
            Updated finding or None
        """
        finding = self.db.query(ValidationFindingModel).filter(
            ValidationFindingModel.id == finding_id,
            ValidationFindingModel.hospital_id == hospital_id
        ).first()
        
        if not finding:
            return None
        
        finding.status = "fixed"
        finding.fixed_by = user_id
        finding.fixed_at = datetime.now(timezone.utc)
        finding.updated_at = datetime.now(timezone.utc)
        
        self.db.commit()
        self.db.refresh(finding)
        
        logger.info(f"[FINDING_FIXED] ID: {finding_id}, User: {user_id}")
        
        return finding
    
    def dismiss_finding(
        self,
        finding_id: str,
        user_id: str,
        hospital_id: str,
        reason: Optional[str] = None
    ) -> Optional[ValidationFindingModel]:
        """
        Dismiss a validation finding.
        
        Args:
            finding_id: Finding ID
            user_id: User ID dismissing the finding
            hospital_id: Hospital ID for access control
            reason: Reason for dismissal
            
        Returns:
            Updated finding or None
        """
        finding = self.db.query(ValidationFindingModel).filter(
            ValidationFindingModel.id == finding_id,
            ValidationFindingModel.hospital_id == hospital_id
        ).first()
        
        if not finding:
            return None
        
        finding.status = "dismissed"
        finding.acknowledged_by = user_id
        finding.acknowledged_at = datetime.now(timezone.utc)
        finding.updated_at = datetime.now(timezone.utc)
        
        if reason:
            finding.explanation = f"{finding.explanation} [Dismissed: {reason}]"
        
        self.db.commit()
        self.db.refresh(finding)
        
        logger.info(f"[FINDING_DISMISSED] ID: {finding_id}, User: {user_id}, Reason: {reason}")
        
        return finding
    
    def revalidate_claim(
        self,
        claim_id: str,
        hospital_id: str,
        documents: List[Dict[str, Any]],
        clinical_data_list: List[Dict[str, Any]],
        claim_data: Dict[str, Any],
        ocr_texts: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """
        Re-validate a claim (clears old findings and creates new ones).
        
        Args:
            claim_id: Claim ID
            hospital_id: Hospital ID
            documents: List of uploaded documents
            clinical_data_list: List of clinical data
            claim_data: Master claim data
            ocr_texts: OCR texts dictionary
            
        Returns:
            dict with new validation results
        """
        # Delete old findings
        self.db.query(ValidationFindingModel).filter(
            ValidationFindingModel.claim_id == claim_id,
            ValidationFindingModel.hospital_id == hospital_id
        ).delete()
        
        self.db.commit()
        
        logger.info(f"[CLAIM_REVALIDATION] Cleared old findings for Claim ID: {claim_id}")
        
        # Run validation again
        return self.validate_claim(
            claim_id,
            hospital_id,
            documents,
            clinical_data_list,
            claim_data,
            ocr_texts
        )


def get_validation_service(db: Session) -> ClaimValidationService:
    """Factory function to get validation service instance"""
    return ClaimValidationService(db)
