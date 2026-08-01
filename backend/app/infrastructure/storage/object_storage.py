from abc import ABC, abstractmethod
import os
import shutil
import hashlib
from typing import Optional, Dict, Any

class IObjectStorageAdapter(ABC):
    """
    Abstract Base Interface for Object Storage Providers (S3, Local Storage, MinIO).
    """
    @abstractmethod
    async def save_bytes(self, key: str, data: bytes, content_type: str) -> str:
        pass

    @abstractmethod
    async def get_bytes(self, key: str) -> bytes:
        pass

    @abstractmethod
    async def delete_object(self, key: str) -> bool:
        pass

    @abstractmethod
    async def generate_presigned_download_url(self, key: str, expires_in_seconds: int = 3600) -> str:
        pass


class LocalObjectStorageAdapter(IObjectStorageAdapter):
    """
    Local Filesystem Object Storage Provider.
    """
    def __init__(self, base_dir: str = "/tmp/ire_object_store"):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    async def save_bytes(self, key: str, data: bytes, content_type: str) -> str:
        file_path = os.path.join(self.base_dir, key.replace("/", "_"))
        with open(file_path, "wb") as f:
            f.write(data)
        return file_path

    async def get_bytes(self, key: str) -> bytes:
        file_path = os.path.join(self.base_dir, key.replace("/", "_"))
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File '{key}' not found in local object store.")
        with open(file_path, "rb") as f:
            return f.read()

    async def delete_object(self, key: str) -> bool:
        file_path = os.path.join(self.base_dir, key.replace("/", "_"))
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False

    async def generate_presigned_download_url(self, key: str, expires_in_seconds: int = 3600) -> str:
        return f"/api/v1/documents/download_stream?key={key}"


class S3ObjectStorageAdapter(IObjectStorageAdapter):
    """
    AWS S3 Object Storage Provider.
    """
    def __init__(self, bucket_name: str = "ire-documents-bucket", region: str = "us-east-1"):
        self.bucket_name = bucket_name
        self.region = region

    async def save_bytes(self, key: str, data: bytes, content_type: str) -> str:
        # S3 Client upload stub
        return f"s3://{self.bucket_name}/{key}"

    async def get_bytes(self, key: str) -> bytes:
        return b"%PDF-1.4 Mock S3 Document Content Data%"

    async def delete_object(self, key: str) -> bool:
        return True

    async def generate_presigned_download_url(self, key: str, expires_in_seconds: int = 3600) -> str:
        return f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{key}?AWSAccessKeyId=MOCK&Signature=MOCK"


class StorageFactory:
    @staticmethod
    def get_storage_adapter(storage_type: str = "LOCAL") -> IObjectStorageAdapter:
        if storage_type.upper() == "S3":
            return S3ObjectStorageAdapter()
        return LocalObjectStorageAdapter()

storage_adapter = StorageFactory.get_storage_adapter()
