import logging
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.future import select

from app.infrastructure.db.models.claim import DocumentModel, RetentionPolicy, VirusScanStatus
from app.infrastructure.storage.storage_backend import StorageService, get_storage_backend

logger = logging.getLogger("retention_service")


class RetentionService:
    """Service for managing document retention policies and cleanup"""
    
    def __init__(self, db: Session):
        self.db = db
        self.storage_service = StorageService(get_storage_backend())
    
    def check_expired_documents(self) -> List[DocumentModel]:
        """
        Find documents that have exceeded their retention policy.
        
        Returns:
            List of documents that should be marked for deletion
        """
        now = datetime.now(timezone.utc)
        
        # Find documents where retention_until has passed
        result = self.db.execute(
            select(DocumentModel).where(
                DocumentModel.retention_until.isnot(None),
                DocumentModel.retention_until < now,
                DocumentModel.marked_for_deletion == 0
            )
        )
        expired_docs = result.scalars().all()
        
        logger.info(f"[RETENTION_CHECK] Found {len(expired_docs)} expired documents")
        
        return expired_docs
    
    def mark_for_deletion(self, document_id: str) -> Optional[DocumentModel]:
        """
        Mark a document for deletion.
        
        Args:
            document_id: ID of the document to mark
            
        Returns:
            Updated document or None if not found
        """
        document = self.db.execute(
            select(DocumentModel).where(DocumentModel.id == document_id)
        ).scalar_one_or_none()
        
        if not document:
            logger.warning(f"[RETENTION_MARK_FAILED] Document not found: {document_id}")
            return None
        
        document.marked_for_deletion = 1
        document.deleted_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(document)
        
        logger.info(f"[RETENTION_MARKED] Document ID: {document_id}")
        
        return document
    
    def delete_marked_documents(self, dry_run: bool = False) -> dict:
        """
        Delete documents that are marked for deletion.
        
        Args:
            dry_run: If True, only report what would be deleted without actually deleting
            
        Returns:
            dict with deletion statistics
        """
        # Find documents marked for deletion
        result = self.db.execute(
            select(DocumentModel).where(DocumentModel.marked_for_deletion == 1)
        )
        marked_docs = result.scalars().all()
        
        stats = {
            "total_marked": len(marked_docs),
            "deleted": 0,
            "failed": 0,
            "skipped": 0,
            "details": []
        }
        
        for document in marked_docs:
            try:
                if dry_run:
                    stats["details"].append({
                        "document_id": document.id,
                        "original_filename": document.original_filename,
                        "internal_filename": document.internal_filename,
                        "marked_for_deletion_at": document.deleted_at.isoformat() if document.deleted_at else None,
                        "action": "would_delete"
                    })
                    stats["skipped"] += 1
                else:
                    # Delete file from storage
                    file_deleted = await self.storage_service.delete_document(
                        internal_filename=document.internal_filename,
                        hospital_id=document.hospital_id
                    )
                    
                    if file_deleted:
                        # Delete database record
                        self.db.delete(document)
                        stats["deleted"] += 1
                        stats["details"].append({
                            "document_id": document.id,
                            "original_filename": document.original_filename,
                            "action": "deleted"
                        })
                        logger.info(f"[RETENTION_DELETED] Document ID: {document.id}")
                    else:
                        stats["failed"] += 1
                        stats["details"].append({
                            "document_id": document.id,
                            "original_filename": document.original_filename,
                            "action": "file_delete_failed"
                        })
                        logger.warning(f"[RETENTION_DELETE_FAILED] Document ID: {document.id}")
                        
            except Exception as e:
                stats["failed"] += 1
                stats["details"].append({
                    "document_id": document.id,
                    "original_filename": document.original_filename,
                    "action": "error",
                    "error": str(e)
                })
                logger.error(f"[RETENTION_DELETE_ERROR] Document ID: {document.id}, Error: {e}")
        
        if not dry_run and stats["deleted"] > 0:
            self.db.commit()
        
        logger.info(f"[RETENTION_CLEANUP] Dry run: {dry_run}, Deleted: {stats['deleted']}, Failed: {stats['failed']}, Skipped: {stats['skipped']}")
        
        return stats
    
    def update_retention_policy(
        self,
        document_id: str,
        policy: RetentionPolicy,
        custom_retention_days: Optional[int] = None
    ) -> Optional[DocumentModel]:
        """
        Update retention policy for a document.
        
        Args:
            document_id: ID of the document
            policy: New retention policy
            custom_retention_days: Custom retention days if policy is CUSTOM
            
        Returns:
            Updated document or None if not found
        """
        document = self.db.execute(
            select(DocumentModel).where(DocumentModel.id == document_id)
        ).scalar_one_or_none()
        
        if not document:
            logger.warning(f"[RETENTION_UPDATE_FAILED] Document not found: {document_id}")
            return None
        
        document.retention_policy = policy.value
        
        # Calculate new retention date
        if policy == RetentionPolicy.PERMANENT:
            document.retention_until = None
        elif policy == RetentionPolicy.DAYS_30:
            document.retention_until = datetime.now(timezone.utc) + __import__('datetime').timedelta(days=30)
        elif policy == RetentionPolicy.DAYS_90:
            document.retention_until = datetime.now(timezone.utc) + __import__('datetime').timedelta(days=90)
        elif policy == RetentionPolicy.DAYS_180:
            document.retention_until = datetime.now(timezone.utc) + __import__('datetime').timedelta(days=180)
        elif policy == RetentionPolicy.DAYS_365:
            document.retention_until = datetime.now(timezone.utc) + __import__('datetime').timedelta(days=365)
        elif policy == RetentionPolicy.CUSTOM and custom_retention_days:
            document.retention_until = datetime.now(timezone.utc) + __import__('datetime').timedelta(days=custom_retention_days)
        
        self.db.commit()
        self.db.refresh(document)
        
        logger.info(f"[RETENTION_UPDATED] Document ID: {document_id}, Policy: {policy.value}")
        
        return document
    
    def get_retention_statistics(self, hospital_id: Optional[str] = None) -> dict:
        """
        Get retention statistics for documents.
        
        Args:
            hospital_id: Optional hospital ID to filter by
            
        Returns:
            dict with retention statistics
        """
        query = select(DocumentModel)
        
        if hospital_id:
            query = query.where(DocumentModel.hospital_id == hospital_id)
        
        result = self.db.execute(query)
        documents = result.scalars().all()
        
        stats = {
            "total_documents": len(documents),
            "by_policy": {},
            "marked_for_deletion": 0,
            "expired_not_marked": 0
        }
        
        now = datetime.now(timezone.utc)
        
        for doc in documents:
            # Count by policy
            policy = doc.retention_policy or "unknown"
            stats["by_policy"][policy] = stats["by_policy"].get(policy, 0) + 1
            
            # Count marked for deletion
            if doc.marked_for_deletion == 1:
                stats["marked_for_deletion"] += 1
            
            # Count expired but not marked
            if doc.retention_until and doc.retention_until < now and doc.marked_for_deletion == 0:
                stats["expired_not_marked"] += 1
        
        return stats
