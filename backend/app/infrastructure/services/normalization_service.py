import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.infrastructure.db.models.claim import NormalizationModel, NormalizationMethod
from app.infrastructure.services.normalization_engine import get_normalization_engine

logger = logging.getLogger("normalization_service")


class NormalizationService:
    """Service for managing data normalization and storing results"""
    
    def __init__(self, db: Session):
        self.db = db
        self.engine = get_normalization_engine()
    
    def normalize_and_store(
        self,
        clinical_data: Dict[str, Any],
        document_id: str,
        hospital_id: str
    ) -> Dict[str, Any]:
        """
        Normalize clinical data and store results in database.
        
        Args:
            clinical_data: Dictionary of extracted clinical data
            document_id: Document ID for tracking
            hospital_id: Hospital ID for tracking
            
        Returns:
            dict with normalized data and normalization results
        """
        # Get normalization results from engine
        normalization_result = self.engine.normalize_clinical_data(
            clinical_data,
            document_id,
            hospital_id
        )
        
        # Store normalization results in database
        for field_name, result in normalization_result["normalization_results"].items():
            try:
                normalization_record = NormalizationModel(
                    document_id=document_id,
                    hospital_id=hospital_id,
                    field_name=result["field_name"],
                    field_type=result.get("field_type", "text"),
                    original_value=result["original_value"],
                    normalized_value=str(result["normalized_value"]) if result["normalized_value"] is not None else None,
                    normalization_method=result["normalization_method"],
                    confidence=result["confidence"],
                    context={
                        "success": result["success"],
                        "field_type": result.get("field_type")
                    }
                )
                self.db.add(normalization_record)
            except Exception as e:
                logger.error(f"[NORMALIZATION_STORE_ERROR] Field: {field_name}, Error: {e}")
        
        self.db.commit()
        
        logger.info(f"[NORMALIZATION_COMPLETE] Document ID: {document_id}, Fields normalized: {len(normalization_result['normalization_results'])}")
        
        return normalization_result
    
    def get_normalizations_for_document(
        self,
        document_id: str,
        hospital_id: str
    ) -> List[NormalizationModel]:
        """
        Get all normalizations for a document.
        
        Args:
            document_id: Document ID
            hospital_id: Hospital ID for access control
            
        Returns:
            List of normalization records
        """
        return self.db.query(NormalizationModel).filter(
            NormalizationModel.document_id == document_id,
            NormalizationModel.hospital_id == hospital_id
        ).all()
    
    def get_normalized_field(
        self,
        document_id: str,
        field_name: str,
        hospital_id: str
    ) -> Optional[NormalizationModel]:
        """
        Get normalization result for a specific field.
        
        Args:
            document_id: Document ID
            field_name: Field name
            hospital_id: Hospital ID for access control
            
        Returns:
            Normalization record or None
        """
        return self.db.query(NormalizationModel).filter(
            NormalizationModel.document_id == document_id,
            NormalizationModel.field_name == field_name,
            NormalizationModel.hospital_id == hospital_id
        ).first()
    
    def get_normalized_clinical_data(
        self,
        document_id: str,
        hospital_id: str
    ) -> Dict[str, Any]:
        """
        Get fully normalized clinical data for a document.
        
        Args:
            document_id: Document ID
            hospital_id: Hospital ID for access control
            
        Returns:
            Dictionary of normalized clinical data
        """
        normalizations = self.get_normalizations_for_document(document_id, hospital_id)
        
        normalized_data = {}
        for norm in normalizations:
            # Convert normalized value back to appropriate type
            if norm.field_type == 'amount' and norm.normalized_value:
                try:
                    normalized_data[norm.field_name] = float(norm.normalized_value)
                except ValueError:
                    normalized_data[norm.field_name] = norm.normalized_value
            else:
                normalized_data[norm.field_name] = norm.normalized_value
        
        return normalized_data
    
    def update_normalization(
        self,
        normalization_id: str,
        normalized_value: str,
        confidence: Optional[float] = None
    ) -> Optional[NormalizationModel]:
        """
        Manually update a normalization result.
        
        Args:
            normalization_id: ID of the normalization record
            normalized_value: New normalized value
            confidence: New confidence score (optional)
            
        Returns:
            Updated normalization record or None
        """
        normalization = self.db.query(NormalizationModel).filter(
            NormalizationModel.id == normalization_id
        ).first()
        
        if not normalization:
            return None
        
        normalization.normalized_value = normalized_value
        if confidence is not None:
            normalization.confidence = confidence
        normalization.updated_at = datetime.now(timezone.utc)
        
        self.db.commit()
        self.db.refresh(normalization)
        
        logger.info(f"[NORMALIZATION_UPDATED] ID: {normalization_id}")
        
        return normalization
    
    def delete_normalizations_for_document(
        self,
        document_id: str,
        hospital_id: str
    ) -> int:
        """
        Delete all normalizations for a document.
        
        Args:
            document_id: Document ID
            hospital_id: Hospital ID for access control
            
        Returns:
            Number of records deleted
        """
        deleted = self.db.query(NormalizationModel).filter(
            NormalizationModel.document_id == document_id,
            NormalizationModel.hospital_id == hospital_id
        ).delete()
        
        self.db.commit()
        
        logger.info(f"[NORMALIZATIONS_DELETED] Document ID: {document_id}, Count: {deleted}")
        
        return deleted
    
    def get_normalization_statistics(
        self,
        hospital_id: str
    ) -> Dict[str, Any]:
        """
        Get normalization statistics for a hospital.
        
        Args:
            hospital_id: Hospital ID
            
        Returns:
            Dictionary with normalization statistics
        """
        normalizations = self.db.query(NormalizationModel).filter(
            NormalizationModel.hospital_id == hospital_id
        ).all()
        
        stats = {
            "total_normalizations": len(normalizations),
            "by_method": {},
            "by_field_type": {},
            "average_confidence": 0.0,
            "high_confidence_count": 0,
            "low_confidence_count": 0
        }
        
        if normalizations:
            total_confidence = 0.0
            for norm in normalizations:
                # Count by method
                method = norm.normalization_method or "unknown"
                stats["by_method"][method] = stats["by_method"].get(method, 0) + 1
                
                # Count by field type
                field_type = norm.field_type or "unknown"
                stats["by_field_type"][field_type] = stats["by_field_type"].get(field_type, 0) + 1
                
                # Confidence tracking
                if norm.confidence:
                    total_confidence += norm.confidence
                    if norm.confidence >= 0.8:
                        stats["high_confidence_count"] += 1
                    elif norm.confidence < 0.5:
                        stats["low_confidence_count"] += 1
            
            stats["average_confidence"] = total_confidence / len(normalizations) if normalizations else 0.0
        
        return stats


def get_normalization_service(db: Session) -> NormalizationService:
    """Factory function to get normalization service instance"""
    return NormalizationService(db)
