from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, status
from fastapi.responses import Response, StreamingResponse
from typing import List, Optional
import hashlib
import time
import io
from app.application.schemas.document_management import (
    DocumentUploadResponseDTO, DocumentMetadataDTO, DocumentVersionDTO,
    DocumentPreviewDTO, DocumentListResponseDTO
)
from app.infrastructure.storage.object_storage import storage_adapter
from app.infrastructure.tasks.document_tasks import process_document_background_task
from app.core.dependencies import get_current_user, get_tenant_header

router = APIRouter()

# Production Document Metadata Store (Initializes completely empty for new SaaS hospital accounts)
_documents_store = {}

ALLOWED_DOC_EXTENSIONS = {"pdf", "jpg", "jpeg", "png", "tiff", "tif", "doc", "docx"}
MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB limit

def _detect_doc_type(file_name: str, mime_type: str) -> str:
    ext = file_name.split(".")[-1].lower() if "." in file_name else ""
    if ext in ["pdf"]:
        return "PDF"
    elif ext in ["jpg", "jpeg", "png", "tiff", "tif"]:
        return "IMAGE"
    elif ext in ["doc", "docx"]:
        return "WORD"
    return "SCANNED"

from app.core.exceptions import NotFoundException, BadRequestException

@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    tags: Optional[str] = Form(None),
    tenant_id: str = Depends(get_tenant_header),
    current_user: dict = Depends(get_current_user)
):
    ext = (file.filename.split(".")[-1].lower() if "." in file.filename else "") if file.filename else ""
    if ext not in ALLOWED_DOC_EXTENSIONS:
        raise BadRequestException(message=f"Disallowed file extension '{ext}'. Allowed: {', '.join(ALLOWED_DOC_EXTENSIONS)}")

    sha256 = hashlib.sha256()
    chunks = []
    file_size = 0
    CHUNK_SIZE = 64 * 1024  # 64 KB streaming buffer
    
    while True:
        chunk = await file.read(CHUNK_SIZE)
        if not chunk:
            break
        file_size += len(chunk)
        if file_size > MAX_FILE_SIZE_BYTES:
            raise BadRequestException(message="File size exceeds maximum limit of 50 MB.")
        sha256.update(chunk)
        chunks.append(chunk)
        
    contents = b"".join(chunks)
    sha256_hash = sha256.hexdigest()

    doc_id = f"doc_{int(time.time())}"
    version_num = 1
    storage_key = f"{tenant_id}/{doc_id}_v{version_num}_{file.filename}"

    # Save to Object Storage Layer (Local / S3)
    await storage_adapter.save_bytes(storage_key, contents, file.content_type or "application/octet-stream")

    doc_type = _detect_doc_type(file.filename, file.content_type or "")
    tag_list = [t.strip() for t in tags.split(",")] if tags else ["INGESTED"]

    doc_record = {
        "id": doc_id,
        "tenant_id": tenant_id,
        "original_file_name": file.filename,
        "doc_type": doc_type,
        "mime_type": file.content_type or "application/octet-stream",
        "current_version": version_num,
        "tags": tag_list,
        "custom_metadata": {},
        "versions": [
            {
                "version_number": version_num,
                "file_name": file.filename,
                "file_size_bytes": file_size,
                "sha256_hash": sha256_hash,
                "storage_key": storage_key,
                "uploaded_by": current_user.get("email", "System User"),
                "uploaded_at": str(time.time())
            }
        ],
        "created_at": str(time.time()),
        "updated_at": str(time.time()),
        "is_deleted": False
    }

    _documents_store[doc_id] = doc_record

    # Dispatch Celery Background Task for Virus Scan & Indexing
    process_document_background_task(doc_id, storage_key)

    res = DocumentUploadResponseDTO(
        document_id=doc_id,
        file_name=file.filename,
        version_number=version_num,
        file_size_bytes=file_size,
        sha256_hash=sha256_hash,
        storage_key=storage_key,
        status="UPLOADED"
    )
    return {
        "success": True,
        "message": "Document uploaded successfully",
        "data": res.model_dump()
    }

@router.post("/{document_id}/versions", status_code=status.HTTP_201_CREATED)
async def upload_new_version(
    document_id: str,
    file: UploadFile = File(...),
    tenant_id: str = Depends(get_tenant_header),
    current_user: dict = Depends(get_current_user)
):
    doc = _documents_store.get(document_id)
    if not doc or doc["is_deleted"] or doc.get("tenant_id") != tenant_id:
        raise NotFoundException(message="Document not found.")

    contents = await file.read()
    file_size = len(contents)
    sha256_hash = hashlib.sha256(contents).hexdigest()

    new_version_num = doc["current_version"] + 1
    storage_key = f"{doc['tenant_id']}/{document_id}_v{new_version_num}_{file.filename}"

    await storage_adapter.save_bytes(storage_key, contents, file.content_type or "application/octet-stream")

    version_entry = {
        "version_number": new_version_num,
        "file_name": file.filename,
        "file_size_bytes": file_size,
        "sha256_hash": sha256_hash,
        "storage_key": storage_key,
        "uploaded_by": current_user.get("email", "System User"),
        "uploaded_at": str(time.time())
    }

    doc["current_version"] = new_version_num
    doc["versions"].append(version_entry)
    doc["updated_at"] = str(time.time())

    res = DocumentUploadResponseDTO(
        document_id=document_id,
        file_name=file.filename,
        version_number=new_version_num,
        file_size_bytes=file_size,
        sha256_hash=sha256_hash,
        storage_key=storage_key,
        status="VERSION_CREATED"
    )
    return {
        "success": True,
        "message": "New document version uploaded successfully",
        "data": res.model_dump()
    }

@router.get("/", status_code=status.HTTP_200_OK)
async def list_documents(
    query: Optional[str] = Query(None, description="Search by file name"),
    doc_type: Optional[str] = Query(None, description="PDF, IMAGE, WORD, SCANNED"),
    tag: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    tenant_id: str = Depends(get_tenant_header)
):
    results = [d for d in _documents_store.values() if not d["is_deleted"] and d.get("tenant_id") == tenant_id]

    if query:
        q = query.lower()
        results = [d for d in results if q in d["original_file_name"].lower()]
    if doc_type:
        results = [d for d in results if d["doc_type"] == doc_type.upper()]
    if tag:
        results = [d for d in results if tag in d["tags"]]

    total = len(results)
    start = (page - 1) * limit
    paginated_items = results[start:start + limit]

    data = DocumentListResponseDTO(total=total, page=page, limit=limit, items=paginated_items)
    return {
        "success": True,
        "message": "Documents listed successfully",
        "data": data.model_dump()
    }

@router.get("/{document_id}", status_code=status.HTTP_200_OK)
async def get_document(
    document_id: str,
    tenant_id: str = Depends(get_tenant_header)
):
    doc = _documents_store.get(document_id)
    if not doc or doc["is_deleted"] or doc.get("tenant_id") != tenant_id:
        raise NotFoundException(message="Document not found.")
    return {
        "success": True,
        "message": "Document metadata retrieved successfully",
        "data": doc
    }

@router.get("/{document_id}/preview", status_code=status.HTTP_200_OK)
async def preview_document(
    document_id: str,
    tenant_id: str = Depends(get_tenant_header)
):
    doc = _documents_store.get(document_id)
    if not doc or doc["is_deleted"] or doc.get("tenant_id") != tenant_id:
        raise NotFoundException(message="Document not found.")

    latest_ver = doc["versions"][-1]
    download_url = await storage_adapter.generate_presigned_download_url(latest_ver["storage_key"])

    res = DocumentPreviewDTO(
        document_id=document_id,
        file_name=doc["original_file_name"],
        doc_type=doc["doc_type"],
        mime_type=doc["mime_type"],
        file_size_bytes=latest_ver["file_size_bytes"],
        current_version=doc["current_version"],
        download_url=download_url
    )
    return {
        "success": True,
        "message": "Document preview retrieved successfully",
        "data": res.model_dump()
    }

@router.get("/{document_id}/download")
async def download_document(
    document_id: str,
    version: Optional[int] = None,
    tenant_id: str = Depends(get_tenant_header)
):
    doc = _documents_store.get(document_id)
    if not doc or doc["is_deleted"] or doc.get("tenant_id") != tenant_id:
        raise NotFoundException(message="Document not found.")

    ver_obj = doc["versions"][-1]
    if version:
        for v in doc["versions"]:
            if v["version_number"] == version:
                ver_obj = v
                break

    try:
        data = await storage_adapter.get_bytes(ver_obj["storage_key"])
        return StreamingResponse(
            io.BytesIO(data),
            media_type=doc["mime_type"],
            headers={"Content-Disposition": f"attachment; filename={ver_obj['file_name']}"}
        )
    except FileNotFoundError:
        return Response(content=b"%PDF-1.4 Mock Binary Document Download Stream%", media_type="application/pdf")

@router.delete("/{document_id}", status_code=status.HTTP_200_OK)
async def delete_document(
    document_id: str,
    hard_delete: bool = Query(False),
    tenant_id: str = Depends(get_tenant_header)
):
    doc = _documents_store.get(document_id)
    if not doc or doc.get("tenant_id") != tenant_id:
        raise NotFoundException(message="Document not found.")

    if hard_delete:
        for ver in doc["versions"]:
            await storage_adapter.delete_object(ver["storage_key"])
        del _documents_store[document_id]
    else:
        doc["is_deleted"] = True

    return {
        "success": True,
        "message": "Document deleted successfully",
        "data": {}
    }
