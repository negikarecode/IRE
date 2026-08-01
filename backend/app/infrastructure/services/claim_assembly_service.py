import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models.claim import (
    DocumentModel, DocumentClaimModel, DocumentClaimStatus, DocumentType
)

logger = logging.getLogger("claim_assembly_service")

class ClaimAssemblyService:
    """Service for assembling documents into insurance claims."""
    
    def __init__(self):
        # Define required document types for a complete claim
        self.required_document_types = [
            DocumentType.DISCHARGE_SUMMARY.value,
            DocumentType.FINAL_BILL.value,
            DocumentType.OPERATIVE_NOTE.value,
            DocumentType.PRESCRIPTION.value,
            DocumentType.AUTHORIZATION_LETTER.value
        ]
        
        # Optional but recommended document types
        self.optional_document_types = [
            DocumentType.LAB_REPORT.value,
            DocumentType.RADIOLOGY_REPORT.value,
            DocumentType.INVESTIGATION_REPORT.value,
            DocumentType.CONSENT_FORM.value,
            DocumentType.INSURANCE_FORM.value
        ]
    
    async def create_claim(
        self,
        hospital_id: str,
        created_by: str,
        document_ids: List[str] = None,
        db: AsyncSession = None
    ) -> DocumentClaimModel:
        """
        Create a new document claim.
        
        Args:
            hospital_id: ID of the hospital
            created_by: ID of the user creating the claim
            document_ids: List of document IDs to link to the claim
            db: Database session
            
        Returns:
            Created DocumentClaimModel instance
        """
        # Generate unique claim number
        claim_number = self._generate_claim_number()
        
        logger.info(f"[CLAIM_CREATE] Hospital ID: {hospital_id}, Claim Number: {claim_number}")
        
        # Create claim record
        claim = DocumentClaimModel(
            id=str(uuid.uuid4()),
            hospital_id=hospital_id,
            claim_number=claim_number,
            status=DocumentClaimStatus.DRAFT.value,
            required_document_types=self.required_document_types,
            missing_document_types=self.required_document_types.copy(),  # Initially all are missing
            created_by=created_by,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        db.add(claim)
        await db.commit()
        await db.refresh(claim)
        
        # Link documents if provided
        if document_ids:
            await self.link_documents_to_claim(claim.id, document_ids, db)
        
        logger.info(f"[CLAIM_CREATED] Claim ID: {claim.id}, Number: {claim_number}")
        
        return claim
    
    async def link_documents_to_claim(
        self,
        claim_id: str,
        document_ids: List[str],
        db: AsyncSession = None
    ) -> None:
        """
        Link documents to a claim.
        
        Args:
            claim_id: ID of the claim
            document_ids: List of document IDs to link
            db: Database session
        """
        logger.info(f"[CLAIM_LINK] Claim ID: {claim_id}, Documents: {len(document_ids)}")
        
        # Update documents with claim_id
        for doc_id in document_ids:
            await db.execute(
                update(DocumentModel)
                .where(DocumentModel.id == doc_id)
                .values(claim_id=claim_id)
            )
        
        await db.commit()
        
        # Update claim status and missing documents
        await self._update_claim_status(claim_id, db)
        
        logger.info(f"[CLAIM_LINKED] Claim ID: {claim_id}, Documents linked successfully")
    
    async def unlink_document_from_claim(
        self,
        document_id: str,
        db: AsyncSession = None
    ) -> None:
        """
        Unlink a document from its claim.
        
        Args:
            document_id: ID of the document to unlink
            db: Database session
        """
        # Get document to find claim_id
        result = await db.execute(
            select(DocumentModel).where(DocumentModel.id == document_id)
        )
        document = result.scalar_one_or_none()
        
        if not document or not document.claim_id:
            logger.warning(f"[CLAIM_UNLINK] Document {document_id} not linked to any claim")
            return
        
        claim_id = document.claim_id
        
        # Remove claim_id from document
        await db.execute(
            update(DocumentModel)
            .where(DocumentModel.id == document_id)
            .values(claim_id=None)
        )
        
        await db.commit()
        
        # Update claim status
        await self._update_claim_status(claim_id, db)
        
        logger.info(f"[CLAIM_UNLINKED] Document ID: {document_id}, Claim ID: {claim_id}")
    
    async def _update_claim_status(
        self,
        claim_id: str,
        db: AsyncSession = None
    ) -> None:
        """
        Update claim status based on linked documents.
        
        Args:
            claim_id: ID of the claim
            db: Database session
        """
        # Get claim
        result = await db.execute(
            select(DocumentClaimModel).where(DocumentClaimModel.id == claim_id)
        )
        claim = result.scalar_one_or_none()
        
        if not claim:
            logger.error(f"[CLAIM_STATUS_UPDATE] Claim {claim_id} not found")
            return
        
        # Get all documents linked to this claim
        result = await db.execute(
            select(DocumentModel).where(DocumentModel.claim_id == claim_id)
        )
        documents = result.scalars().all()
        
        # Extract document types
        linked_types = set()
        for doc in documents:
            if doc.document_type:
                linked_types.add(doc.document_type)
        
        # Calculate missing required document types
        missing_required = [
            req_type for req_type in claim.required_document_types
            if req_type not in linked_types
        ]
        
        # Update claim
        claim.missing_document_types = missing_required
        
        # Determine status based on completeness
        if not missing_required:
            claim.status = DocumentClaimStatus.READY_FOR_REVIEW.value
        elif len(linked_types) > 0:
            claim.status = DocumentClaimStatus.DRAFT.value
        else:
            claim.status = DocumentClaimStatus.DRAFT.value
        
        claim.updated_at = datetime.now(timezone.utc)
        
        await db.commit()
        
        logger.info(f"[CLAIM_STATUS_UPDATED] Claim ID: {claim_id}, Status: {claim.status}, Missing: {len(missing_required)}")
    
    async def get_claim_documents(
        self,
        claim_id: str,
        db: AsyncSession = None
    ) -> List[DocumentModel]:
        """
        Get all documents linked to a claim.
        
        Args:
            claim_id: ID of the claim
            db: Database session
            
        Returns:
            List of DocumentModel instances
        """
        result = await db.execute(
            select(DocumentModel).where(DocumentModel.claim_id == claim_id)
        )
        documents = result.scalars().all()
        
        return list(documents)
    
    async def get_claim_summary(
        self,
        claim_id: str,
        db: AsyncSession = None
    ) -> Dict:
        """
        Get summary of a claim including document counts and status.
        
        Args:
            claim_id: ID of the claim
            db: Database session
            
        Returns:
            Dictionary containing claim summary
        """
        # Get claim
        result = await db.execute(
            select(DocumentClaimModel).where(DocumentClaimModel.id == claim_id)
        )
        claim = result.scalar_one_or_none()
        
        if not claim:
            return None
        
        # Get documents
        documents = await self.get_claim_documents(claim_id, db)
        
        # Count by document type
        type_counts = {}
        for doc in documents:
            doc_type = doc.document_type or 'unknown'
            type_counts[doc_type] = type_counts.get(doc_type, 0) + 1
        
        return {
            'claim_id': claim.id,
            'claim_number': claim.claim_number,
            'status': claim.status,
            'total_documents': len(documents),
            'document_type_counts': type_counts,
            'required_document_types': claim.required_document_types,
            'missing_document_types': claim.missing_document_types,
            'is_complete': len(claim.missing_document_types) == 0,
            'created_at': claim.created_at.isoformat(),
            'updated_at': claim.updated_at.isoformat()
        }
    
    def _generate_claim_number(self) -> str:
        """Generate a unique claim number."""
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
        random_suffix = str(uuid.uuid4())[:8].upper()
        return f"CLM-{timestamp}-{random_suffix}"
    
    async def auto_group_documents(
        self,
        hospital_id: str,
        user_id: str,
        db: AsyncSession = None
    ) -> List[DocumentClaimModel]:
        """
        Automatically group unlinked documents into claims based on clinical data.
        
        Args:
            hospital_id: ID of the hospital
            user_id: ID of the user
            db: Database session
            
        Returns:
            List of created DocumentClaimModel instances
        """
        logger.info(f"[AUTO_GROUP] Hospital ID: {hospital_id}")
        
        # Get all unlinked documents for the hospital
        result = await db.execute(
            select(DocumentModel).where(
                DocumentModel.hospital_id == hospital_id,
                DocumentModel.claim_id.is_(None)
            )
        )
        unlinked_documents = result.scalars().all()
        
        if not unlinked_documents:
            logger.info(f"[AUTO_GROUP] No unlinked documents found")
            return []
        
        # Group documents by patient info (UHID, MRN, patient name from clinical extraction)
        # For now, we'll create a simple grouping by upload batch
        # In production, this would use clinical extraction data to group by patient
        
        # Create one claim per 5 documents as a simple heuristic
        batch_size = 5
        created_claims = []
        
        for i in range(0, len(unlinked_documents), batch_size):
            batch = unlinked_documents[i:i + batch_size]
            document_ids = [doc.id for doc in batch]
            
            claim = await self.create_claim(
                hospital_id=hospital_id,
                created_by=user_id,
                document_ids=document_ids,
                db=db
            )
            
            created_claims.append(claim)
        
        logger.info(f"[AUTO_GROUP_COMPLETE] Created {len(created_claims)} claims")
        
        return created_claims


# Singleton instance
claim_assembly_service = ClaimAssemblyService()
