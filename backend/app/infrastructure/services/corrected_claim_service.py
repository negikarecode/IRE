from __future__ import annotations
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
import copy

from app.infrastructure.db.models.claim import (
    CorrectedClaimPreviewModel, ClaimChangeModel, ClaimChangeStatus
)
from app.infrastructure.base.ai_recommendation import RecommendationBuilder

logger = logging.getLogger("corrected_claim_service")


class CorrectedClaimService:
    """Service for generating and managing corrected claim previews"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def generate_corrected_claim(
        self,
        claim_id: str,
        hospital_id: str,
        original_claim_data: Dict[str, Any],
        validation_findings: List[Dict] = None,
        coding_findings: List[Dict] = None,
        leakage_findings: List[Dict] = None
    ) -> Dict[str, Any]:
        """
        Generate a corrected claim preview based on AI recommendations.
        
        Args:
            claim_id: Claim ID
            hospital_id: Hospital ID
            original_claim_data: Original claim data
            validation_findings: Validation recommendations
            coding_findings: Coding review recommendations
            leakage_findings: Revenue leakage recommendations
            
        Returns:
            dict with corrected claim preview and changes
        """
        logger.info(f"[CORRECTED_CLAIM_GENERATION] Claim ID: {claim_id}")
        
        # Create a copy of original claim for corrections
        corrected_claim = copy.deepcopy(original_claim_data)
        
        # Track all changes
        all_changes = []
        
        # Apply validation-based corrections
        if validation_findings:
            validation_changes = self._apply_validation_corrections(
                corrected_claim, validation_findings, claim_id, hospital_id
            )
            all_changes.extend(validation_changes)
        
        # Apply coding-based corrections
        if coding_findings:
            coding_changes = self._apply_coding_corrections(
                corrected_claim, coding_findings, claim_id, hospital_id
            )
            all_changes.extend(coding_changes)
        
        # Apply leakage-based corrections
        if leakage_findings:
            leakage_changes = self._apply_leakage_corrections(
                corrected_claim, leakage_findings, claim_id, hospital_id
            )
            all_changes.extend(leakage_changes)
        
        # Store preview in database
        preview_id = self._store_preview(
            claim_id,
            hospital_id,
            original_claim_data,
            corrected_claim,
            all_changes,
            validation_findings + (coding_findings or []) + (leakage_findings or [])
        )
        
        # Store changes in database
        self._store_changes(all_changes, preview_id, claim_id, hospital_id)
        
        logger.info(f"[CORRECTED_CLAIM_COMPLETE] Claim ID: {claim_id}, Changes: {len(all_changes)}")
        
        return {
            "preview_id": preview_id,
            "claim_id": claim_id,
            "hospital_id": hospital_id,
            "original_claim": original_claim_data,
            "corrected_claim": corrected_claim,
            "changes": [change.to_dict() for change in all_changes],
            "total_changes": len(all_changes),
            "status": "pending"
        }
    
    def _apply_validation_corrections(
        self,
        corrected_claim: Dict[str, Any],
        findings: List[Dict],
        claim_id: str,
        hospital_id: str
    ) -> List[ClaimChange]:
        """Apply validation-based corrections"""
        changes = []
        
        clinical_data = corrected_claim.get("clinical_data", {})
        
        for finding in findings:
            # Extract field to correct from finding
            affected_field = finding.get("relevant_extracted_fields", {}).get("affected_field")
            recommended_fix = finding.get("recommended_action")
            
            if not affected_field or not recommended_fix:
                continue
            
            original_value = clinical_data.get(affected_field)
            
            # Determine corrected value based on recommendation
            corrected_value = self._extract_corrected_value(recommended_fix, original_value)
            
            if corrected_value and corrected_value != original_value:
                change = ClaimChange(
                    field_name=affected_field,
                    original_value=str(original_value) if original_value else None,
                    corrected_value=str(corrected_value),
                    change_type="modify" if original_value else "add",
                    source="validation",
                    source_finding_id=finding.get("relevant_extracted_fields", {}).get("id"),
                    ai_recommendation=finding
                )
                changes.append(change)
                
                # Apply correction to claim
                clinical_data[affected_field] = corrected_value
        
        return changes
    
    def _apply_coding_corrections(
        self,
        corrected_claim: Dict[str, Any],
        findings: List[Dict],
        claim_id: str,
        hospital_id: str
    ) -> List[ClaimChange]:
        """Apply coding-based corrections"""
        changes = []
        
        clinical_data = corrected_claim.get("clinical_data", {})
        
        for finding in findings:
            affected_code = finding.get("relevant_extracted_fields", {}).get("affected_code")
            recommended_action = finding.get("recommended_action")
            
            if not affected_code or not recommended_action:
                continue
            
            # Determine which field to correct (ICD or CPT)
            code_type = finding.get("relevant_extracted_fields", {}).get("code_type", "").lower()
            
            if code_type == "icd":
                field_name = "icd_codes"
            elif code_type == "cpt":
                field_name = "cpt_codes"
            else:
                continue
            
            original_value = clinical_data.get(field_name, "")
            corrected_value = self._extract_corrected_code(recommended_action, affected_code, original_value)
            
            if corrected_value and corrected_value != original_value:
                change = ClaimChange(
                    field_name=field_name,
                    original_value=original_value,
                    corrected_value=corrected_value,
                    change_type="modify",
                    source="coding_review",
                    source_finding_id=finding.get("relevant_extracted_fields", {}).get("id"),
                    ai_recommendation=finding
                )
                changes.append(change)
                
                # Apply correction to claim
                clinical_data[field_name] = corrected_value
        
        return changes
    
    def _apply_leakage_corrections(
        self,
        corrected_claim: Dict[str, Any],
        findings: List[Dict],
        claim_id: str,
        hospital_id: str
    ) -> List[ClaimChange]:
        """Apply revenue leakage-based corrections"""
        changes = []
        
        clinical_data = corrected_claim.get("clinical_data", {})
        
        for finding in findings:
            affected_code = finding.get("affected_code")
            recommended_action = finding.get("recommended_action")
            
            if not recommended_action:
                continue
            
            # Determine field to correct
            category = finding.get("category", "")
            
            if category == "missing_procedure":
                field_name = "cpt_codes"
            elif category == "missed_diagnosis":
                field_name = "icd_codes"
            elif category == "missing_modifier":
                field_name = "cpt_codes"
            elif category == "underbilling":
                field_name = "bill_amount"
            else:
                continue
            
            original_value = clinical_data.get(field_name)
            
            if category == "underbilling":
                # Handle bill amount correction
                corrected_value = self._extract_corrected_amount(recommended_action, original_value)
            else:
                # Handle code corrections
                corrected_value = self._extract_corrected_code(recommended_action, affected_code, original_value)
            
            if corrected_value and corrected_value != original_value:
                change = ClaimChange(
                    field_name=field_name,
                    original_value=str(original_value) if original_value else None,
                    corrected_value=str(corrected_value),
                    change_type="add" if not original_value else "modify",
                    source="revenue_leakage",
                    source_finding_id=finding.get("relevant_extracted_fields", {}).get("id"),
                    ai_recommendation=finding
                )
                changes.append(change)
                
                # Apply correction to claim
                clinical_data[field_name] = corrected_value
        
        return changes
    
    def _extract_corrected_value(self, recommendation: str, original_value: Any) -> Any:
        """Extract corrected value from recommendation"""
        # Simple extraction - in production, use NLP to parse recommendations
        if "Add" in recommendation or "Include" in recommendation:
            # Extract the value to add
            import re
            match = re.search(r'[A-Z]\d{2}(?:\.\d+)?', recommendation)
            if match:
                return match.group(0)
        return original_value
    
    def _extract_corrected_code(self, recommendation: str, old_code: str, original_value: str) -> str:
        """Extract corrected code from recommendation"""
        # Extract new code from recommendation
        import re
        codes = re.findall(r'[A-Z]?\d{5}(?:-\d{2})?', recommendation)
        if codes:
            new_code = codes[0]
            # Replace old code with new code in the list
            if original_value:
                codes_list = [c.strip() for c in str(original_value).split(",")]
                if old_code in codes_list:
                    codes_list[codes_list.index(old_code)] = new_code
                else:
                    codes_list.append(new_code)
                return ", ".join(codes_list)
            return new_code
        return original_value
    
    def _extract_corrected_amount(self, recommendation: str, original_value: Any) -> float:
        """Extract corrected amount from recommendation"""
        import re
        amounts = re.findall(r'₹?([\d,]+\.?\d*)', recommendation)
        if amounts:
            try:
                return float(amounts[0].replace(",", ""))
            except ValueError:
                pass
        return original_value
    
    def _store_preview(
        self,
        claim_id: str,
        hospital_id: str,
        original_claim_data: Dict[str, Any],
        corrected_claim_data: Dict[str, Any],
        changes: List,
        ai_recommendations: List[Dict]
    ) -> str:
        """Store corrected claim preview in database"""
        preview_id = str(__import__('uuid').uuid4())
        
        preview_record = CorrectedClaimPreviewModel(
            id=preview_id,
            claim_id=claim_id,
            hospital_id=hospital_id,
            original_claim_data=original_claim_data,
            corrected_claim_data=corrected_claim_data,
            ai_recommendations=ai_recommendations,
            status="pending",
            total_changes=len(changes)
        )
        
        # Update existing preview or create new
        existing = self.db.query(CorrectedClaimPreviewModel).filter(
            CorrectedClaimPreviewModel.claim_id == claim_id
        ).first()
        
        if existing:
            existing.original_claim_data = original_claim_data
            existing.corrected_claim_data = corrected_claim_data
            existing.ai_recommendations = ai_recommendations
            existing.status = "pending"
            existing.total_changes = len(changes)
            existing.accepted_changes = 0
            existing.rejected_changes = 0
            existing.updated_at = datetime.now(timezone.utc)
            preview_id = existing.id
        else:
            self.db.add(preview_record)
        
        self.db.commit()
        
        return preview_id
    
    def _store_changes(
        self,
        changes: List,
        preview_id: str,
        claim_id: str,
        hospital_id: str
    ):
        """Store individual changes in database"""
        # Delete old changes for this preview
        self.db.query(ClaimChangeModel).filter(
            ClaimChangeModel.preview_id == preview_id
        ).delete()
        
        for change in changes:
            change_record = ClaimChangeModel(
                id=str(__import__('uuid').uuid4()),
                preview_id=preview_id,
                claim_id=claim_id,
                hospital_id=hospital_id,
                field_name=change.field_name,
                original_value=change.original_value,
                corrected_value=change.corrected_value,
                change_type=change.change_type,
                source=change.source,
                source_finding_id=change.source_finding_id,
                status="pending",
                ai_recommendation=change.ai_recommendation
            )
            self.db.add(change_record)
        
        self.db.commit()
    
    def accept_change(
        self,
        change_id: str,
        user_id: str,
        hospital_id: str
    ) -> Optional[ClaimChangeModel]:
        """Accept a proposed change"""
        change = self.db.query(ClaimChangeModel).filter(
            ClaimChangeModel.id == change_id,
            ClaimChangeModel.hospital_id == hospital_id
        ).first()
        
        if not change:
            return None
        
        change.status = ClaimChangeStatus.ACCEPTED.value
        change.accepted_by = user_id
        change.accepted_at = datetime.now(timezone.utc)
        change.updated_at = datetime.now(timezone.utc)
        
        # Update preview summary
        self._update_preview_summary(change.preview_id)
        
        self.db.commit()
        self.db.refresh(change)
        
        logger.info(f"[CHANGE_ACCEPTED] ID: {change_id}, User: {user_id}")
        
        return change
    
    def reject_change(
        self,
        change_id: str,
        user_id: str,
        hospital_id: str
    ) -> Optional[ClaimChangeModel]:
        """Reject a proposed change"""
        change = self.db.query(ClaimChangeModel).filter(
            ClaimChangeModel.id == change_id,
            ClaimChangeModel.hospital_id == hospital_id
        ).first()
        
        if not change:
            return None
        
        change.status = ClaimChangeStatus.REJECTED.value
        change.rejected_by = user_id
        change.rejected_at = datetime.now(timezone.utc)
        change.updated_at = datetime.now(timezone.utc)
        
        # Update preview summary
        self._update_preview_summary(change.preview_id)
        
        self.db.commit()
        self.db.refresh(change)
        
        logger.info(f"[CHANGE_REJECTED] ID: {change_id}, User: {user_id}")
        
        return change
    
    def edit_change(
        self,
        change_id: str,
        edited_value: str,
        user_id: str,
        hospital_id: str
    ) -> Optional[ClaimChangeModel]:
        """Edit a proposed change with user's value"""
        change = self.db.query(ClaimChangeModel).filter(
            ClaimChangeModel.id == change_id,
            ClaimChangeModel.hospital_id == hospital_id
        ).first()
        
        if not change:
            return None
        
        change.status = ClaimChangeStatus.EDITED.value
        change.edited_value = edited_value
        change.edited_by = user_id
        change.edited_at = datetime.now(timezone.utc)
        change.updated_at = datetime.now(timezone.utc)
        
        # Update corrected value
        change.corrected_value = edited_value
        
        # Update preview summary
        self._update_preview_summary(change.preview_id)
        
        self.db.commit()
        self.db.refresh(change)
        
        logger.info(f"[CHANGE_EDITED] ID: {change_id}, User: {user_id}")
        
        return change
    
    def approve_preview(
        self,
        preview_id: str,
        user_id: str,
        hospital_id: str
    ) -> Optional[CorrectedClaimPreviewModel]:
        """Approve the corrected claim preview"""
        preview = self.db.query(CorrectedClaimPreviewModel).filter(
            CorrectedClaimPreviewModel.id == preview_id,
            CorrectedClaimPreviewModel.hospital_id == hospital_id
        ).first()
        
        if not preview:
            return None
        
        # Mark all accepted changes as approved
        changes = self.db.query(ClaimChangeModel).filter(
            ClaimChangeModel.preview_id == preview_id,
            ClaimChangeModel.status.in_([ClaimChangeStatus.ACCEPTED.value, ClaimChangeStatus.EDITED.value])
        ).all()
        
        for change in changes:
            change.status = ClaimChangeStatus.APPROVED.value
        
        preview.status = "approved"
        preview.approved_by = user_id
        preview.approved_at = datetime.now(timezone.utc)
        preview.updated_at = datetime.now(timezone.utc)
        
        self.db.commit()
        self.db.refresh(preview)
        
        logger.info(f"[PREVIEW_APPROVED] ID: {preview_id}, User: {user_id}")
        
        return preview
    
    def get_preview(
        self,
        claim_id: str,
        hospital_id: str
    ) -> Optional[CorrectedClaimPreviewModel]:
        """Get corrected claim preview for a claim"""
        return self.db.query(CorrectedClaimPreviewModel).filter(
            CorrectedClaimPreviewModel.claim_id == claim_id,
            CorrectedClaimPreviewModel.hospital_id == hospital_id
        ).first()
    
    def get_changes(
        self,
        preview_id: str,
        hospital_id: str,
        status: Optional[str] = None
    ) -> List[ClaimChangeModel]:
        """Get changes for a preview"""
        query = self.db.query(ClaimChangeModel).filter(
            ClaimChangeModel.preview_id == preview_id,
            ClaimChangeModel.hospital_id == hospital_id
        )
        
        if status:
            query = query.filter(ClaimChangeModel.status == status)
        
        return query.all()
    
    def _update_preview_summary(self, preview_id: str):
        """Update preview summary with accepted/rejected counts"""
        changes = self.db.query(ClaimChangeModel).filter(
            ClaimChangeModel.preview_id == preview_id
        ).all()
        
        accepted = sum(1 for c in changes if c.status == ClaimChangeStatus.ACCEPTED.value)
        rejected = sum(1 for c in changes if c.status == ClaimChangeStatus.REJECTED.value)
        
        preview = self.db.query(CorrectedClaimPreviewModel).filter(
            CorrectedClaimPreviewModel.id == preview_id
        ).first()
        
        if preview:
            preview.accepted_changes = accepted
            preview.rejected_changes = rejected
            preview.updated_at = datetime.now(timezone.utc)
            self.db.commit()


class ClaimChange:
    """Represents a single claim change"""
    
    def __init__(
        self,
        field_name: str,
        original_value: Optional[str],
        corrected_value: str,
        change_type: str,
        source: str,
        source_finding_id: Optional[str] = None,
        ai_recommendation: Dict[str, Any] = None
    ):
        self.field_name = field_name
        self.original_value = original_value
        self.corrected_value = corrected_value
        self.change_type = change_type
        self.source = source
        self.source_finding_id = source_finding_id
        self.ai_recommendation = ai_recommendation or {}
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "field_name": self.field_name,
            "original_value": self.original_value,
            "corrected_value": self.corrected_value,
            "change_type": self.change_type,
            "source": self.source,
            "source_finding_id": self.source_finding_id,
            "ai_recommendation": self.ai_recommendation
        }


def get_corrected_claim_service(db: Session) -> CorrectedClaimService:
    """Factory function to get corrected claim service instance"""
    return CorrectedClaimService(db)
