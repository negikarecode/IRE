from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class DocumentVersionDTO(BaseModel):
    version_number: int
    file_name: str
    file_size_bytes: int
    sha256_hash: str
    storage_key: str
    uploaded_by: str
    uploaded_at: str

class DocumentMetadataDTO(BaseModel):
    id: str
    tenant_id: str
    original_file_name: str
    doc_type: str  # PDF, JPEG, PNG, TIFF, WORD, SCANNED
    mime_type: str
    current_version: int
    tags: List[str] = []
    custom_metadata: Dict[str, Any] = {}
    versions: List[DocumentVersionDTO] = []
    created_at: str
    updated_at: str
    is_deleted: bool = False

class DocumentUploadResponseDTO(BaseModel):
    document_id: str
    file_name: str
    version_number: int
    file_size_bytes: int
    sha256_hash: str
    storage_key: str
    status: str = "UPLOADED"

class DocumentPreviewDTO(BaseModel):
    document_id: str
    file_name: str
    doc_type: str
    mime_type: str
    file_size_bytes: int
    current_version: int
    download_url: str
    thumbnail_preview_url: Optional[str] = None

class DocumentListResponseDTO(BaseModel):
    total: int
    page: int
    limit: int
    items: List[DocumentMetadataDTO]
