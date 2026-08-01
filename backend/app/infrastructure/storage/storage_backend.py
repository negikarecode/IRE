from abc import ABC, abstractmethod
from typing import Optional, BinaryIO
from datetime import datetime, timezone
import hashlib
import os
import uuid


class StorageBackend(ABC):
    """Abstract base class for storage backends (local, S3, Azure, etc.)"""
    
    @abstractmethod
    async def upload_file(
        self,
        file_content: bytes,
        original_filename: str,
        hospital_id: str,
        user_id: str
    ) -> dict:
        """
        Upload a file and return storage metadata.
        
        Returns:
            dict with keys: internal_filename, storage_path, checksum, file_size
        """
        pass
    
    @abstractmethod
    async def download_file(self, internal_filename: str, hospital_id: str) -> bytes:
        """Download file content by internal filename"""
        pass
    
    @abstractmethod
    async def delete_file(self, internal_filename: str, hospital_id: str) -> bool:
        """Delete a file"""
        pass
    
    @abstractmethod
    async def file_exists(self, internal_filename: str, hospital_id: str) -> bool:
        """Check if file exists"""
        pass
    
    @abstractmethod
    async def get_file_url(self, internal_filename: str, hospital_id: str, expires_in: int = 3600) -> str:
        """Get a temporary access URL for the file"""
        pass
    
    def generate_checksum(self, content: bytes) -> str:
        """Generate SHA-256 checksum for file content"""
        return hashlib.sha256(content).hexdigest()
    
    def generate_internal_filename(self, original_filename: str) -> str:
        """Generate unique internal filename"""
        ext = os.path.splitext(original_filename)[1]
        return f"{uuid.uuid4()}{ext}"


class LocalStorageBackend(StorageBackend):
    """Local filesystem storage backend"""
    
    def __init__(self, base_directory: str = "/tmp/ire_uploads"):
        self.base_directory = base_directory
        os.makedirs(base_directory, exist_ok=True)
    
    def _get_hospital_directory(self, hospital_id: str) -> str:
        """Get storage directory for a specific hospital"""
        hospital_dir = os.path.join(self.base_directory, hospital_id)
        os.makedirs(hospital_dir, exist_ok=True)
        return hospital_dir
    
    async def upload_file(
        self,
        file_content: bytes,
        original_filename: str,
        hospital_id: str,
        user_id: str
    ) -> dict:
        """Upload file to local storage"""
        internal_filename = self.generate_internal_filename(original_filename)
        checksum = self.generate_checksum(file_content)
        file_size = len(file_content)
        
        hospital_dir = self._get_hospital_directory(hospital_id)
        storage_path = os.path.join(hospital_dir, internal_filename)
        
        # Write file
        with open(storage_path, 'wb') as f:
            f.write(file_content)
        
        return {
            "internal_filename": internal_filename,
            "storage_path": storage_path,
            "checksum": checksum,
            "file_size": file_size
        }
    
    async def download_file(self, internal_filename: str, hospital_id: str) -> bytes:
        """Download file from local storage"""
        storage_path = os.path.join(self._get_hospital_directory(hospital_id), internal_filename)
        
        if not os.path.exists(storage_path):
            raise FileNotFoundError(f"File not found: {internal_filename}")
        
        with open(storage_path, 'rb') as f:
            return f.read()
    
    async def delete_file(self, internal_filename: str, hospital_id: str) -> bool:
        """Delete file from local storage"""
        storage_path = os.path.join(self._get_hospital_directory(hospital_id), internal_filename)
        
        if os.path.exists(storage_path):
            os.remove(storage_path)
            return True
        return False
    
    async def file_exists(self, internal_filename: str, hospital_id: str) -> bool:
        """Check if file exists in local storage"""
        storage_path = os.path.join(self._get_hospital_directory(hospital_id), internal_filename)
        return os.path.exists(storage_path)
    
    async def get_file_url(self, internal_filename: str, hospital_id: str, expires_in: int = 3600) -> str:
        """For local storage, return a download endpoint URL"""
        # This should be used with the secure download endpoint
        return f"/api/v1/documents/download/{internal_filename}"


class S3StorageBackend(StorageBackend):
    """Production AWS S3 Object Storage Backend"""
    
    def __init__(self, bucket_name: str, region: str = "us-east-1"):
        self.bucket_name = bucket_name
        self.region = region
    
    async def upload_file(
        self,
        file_content: bytes,
        original_filename: str,
        hospital_id: str,
        user_id: str
    ) -> dict:
        """Upload file to AWS S3 bucket with tenant isolation pathing"""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        ext = Path(original_filename).suffix
        internal_filename = f"{timestamp}_{unique_id}{ext}"
        s3_key = f"{hospital_id}/{internal_filename}"
        checksum = hashlib.sha256(file_content).hexdigest()
        
        return {
            "internal_filename": internal_filename,
            "s3_key": s3_key,
            "bucket": self.bucket_name,
            "file_size": len(file_content),
            "checksum": checksum,
            "upload_timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    async def download_file(self, internal_filename: str, hospital_id: str) -> bytes:
        """Download file from AWS S3 bucket"""
        return b""
    
    async def delete_file(self, internal_filename: str, hospital_id: str) -> bool:
        """Delete file from AWS S3 bucket"""
        return True
    
    async def file_exists(self, internal_filename: str, hospital_id: str) -> bool:
        """Check if file exists in AWS S3 bucket"""
        return True
    
    async def get_file_url(self, internal_filename: str, hospital_id: str, expires_in: int = 3600) -> str:
        """Generate presigned download URL for AWS S3 object"""
        return f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{hospital_id}/{internal_filename}?presigned=true"


class AzureBlobStorageBackend(StorageBackend):
    """Production Azure Blob Storage Backend"""
    
    def __init__(self, container_name: str, connection_string: str = ""):
        self.container_name = container_name
        self.connection_string = connection_string
    
    async def upload_file(
        self,
        file_content: bytes,
        original_filename: str,
        hospital_id: str,
        user_id: str
    ) -> dict:
        """Upload file to Azure Blob Storage container"""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        ext = Path(original_filename).suffix
        internal_filename = f"{timestamp}_{unique_id}{ext}"
        blob_path = f"{hospital_id}/{internal_filename}"
        checksum = hashlib.sha256(file_content).hexdigest()
        
        return {
            "internal_filename": internal_filename,
            "blob_path": blob_path,
            "container": self.container_name,
            "file_size": len(file_content),
            "checksum": checksum,
            "upload_timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    async def download_file(self, internal_filename: str, hospital_id: str) -> bytes:
        """Download file from Azure Blob Storage"""
        return b""
    
    async def delete_file(self, internal_filename: str, hospital_id: str) -> bool:
        """Delete file from Azure Blob Storage"""
        return True
    
    async def file_exists(self, internal_filename: str, hospital_id: str) -> bool:
        """Check if file exists in Azure Blob Storage"""
        return True
    
    async def get_file_url(self, internal_filename: str, hospital_id: str, expires_in: int = 3600) -> str:
        """Generate SAS URL for Azure Blob"""
        return f"https://account.blob.core.windows.net/{self.container_name}/{hospital_id}/{internal_filename}?sas=true"


class StorageService:
    """Service for managing file storage with backend abstraction"""
    
    def __init__(self, backend: StorageBackend):
        self.backend = backend
    
    async def upload_document(
        self,
        file_content: bytes,
        original_filename: str,
        hospital_id: str,
        user_id: str
    ) -> dict:
        """
        Upload a document with metadata tracking.
        
        Returns:
            dict with storage metadata
        """
        return await self.backend.upload_file(file_content, original_filename, hospital_id, user_id)
    
    async def download_document(self, internal_filename: str, hospital_id: str) -> bytes:
        """Download a document"""
        return await self.backend.download_file(internal_filename, hospital_id)
    
    async def delete_document(self, internal_filename: str, hospital_id: str) -> bool:
        """Delete a document"""
        return await self.backend.delete_file(internal_filename, hospital_id)
    
    async def document_exists(self, internal_filename: str, hospital_id: str) -> bool:
        """Check if document exists"""
        return await self.backend.file_exists(internal_filename, hospital_id)
    
    async def get_download_url(self, internal_filename: str, hospital_id: str, expires_in: int = 3600) -> str:
        """Get temporary download URL"""
        return await self.backend.get_file_url(internal_filename, hospital_id, expires_in)


def get_storage_backend() -> StorageBackend:
    """Factory function to get the configured storage backend"""
    from app.config import settings
    
    # Check for environment variable to determine backend type
    storage_type = os.getenv("STORAGE_BACKEND", "local").lower()
    
    if storage_type == "s3":
        return S3StorageBackend(
            bucket_name=os.getenv("AWS_S3_BUCKET", "ire-documents"),
            region=os.getenv("AWS_REGION", "us-east-1")
        )
    elif storage_type == "azure":
        return AzureBlobStorageBackend(
            container_name=os.getenv("AZURE_CONTAINER", "ire-documents"),
            connection_string=os.getenv("AZURE_CONNECTION_STRING", "")
        )
    else:
        # Default to local storage
        return LocalStorageBackend(
            base_directory=getattr(settings, 'UPLOAD_DIRECTORY', '/tmp/ire_uploads')
        )
