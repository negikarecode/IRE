from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Optional
from app.application.schemas.patient_claim import (
    PatientCreateDTO, PatientUpdateDTO, PatientResponseDTO, PatientListResponseDTO,
    ClaimCreateDTO, ClaimUpdateDTO, ClaimAssignDTO, ClaimAddCommentDTO, ClaimAddTagDTO,
    ClaimAttachDocumentDTO, ClaimResponseDTO, ClaimListResponseDTO, ClaimTimelineEventDTO,
    ClaimCommentDTO, ClaimAttachmentDTO
)
from app.core.dependencies import get_current_user, get_tenant_header
import time

router = APIRouter()

# Production Database Stores (Initializes completely empty for new SaaS hospital accounts)
_patients_store = {}
_claims_store = {}
_claim_timelines = {}

# ==============================================================================
# PATIENT MANAGEMENT ENDPOINTS
# ==============================================================================

from app.core.exceptions import NotFoundException

# ==============================================================================
# PATIENT MANAGEMENT ENDPOINTS
# ==============================================================================

@router.post("/patients/", status_code=status.HTTP_201_CREATED)
async def create_patient(
    dto: PatientCreateDTO,
    tenant_id: str = Depends(get_tenant_header),
    current_user: dict = Depends(get_current_user)
):
    patient_id = f"pat_{int(time.time())}"
    patient = {
        "id": patient_id,
        "tenant_id": tenant_id,
        "mrn": dto.mrn,
        "first_name": dto.first_name,
        "last_name": dto.last_name,
        "dob": dto.dob,
        "gender": dto.gender,
        "phone": dto.phone,
        "email": dto.email,
        "hospital_id": dto.hospital_id,
        "created_at": str(time.time())
    }
    _patients_store[patient_id] = patient
    return {
        "success": True,
        "message": "Patient created successfully",
        "data": patient
    }

@router.get("/patients/", status_code=status.HTTP_200_OK)
async def list_patients(
    query: Optional[str] = Query(None, description="Search MRN or Patient Name"),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    sort_by: str = Query("created_at"),
    tenant_id: str = Depends(get_tenant_header)
):
    results = [p for p in _patients_store.values() if p.get("tenant_id") == tenant_id]
    
    if query:
        q = query.lower()
        results = [
            p for p in results 
            if q in p["mrn"].lower() or q in p["first_name"].lower() or q in p["last_name"].lower()
        ]
    
    reverse = sort_by.startswith("-")
    field = sort_by.lstrip("-")
    results = sorted(results, key=lambda x: x.get(field, ""), reverse=reverse)
    
    total = len(results)
    start = (page - 1) * limit
    paginated_items = results[start:start + limit]
    
    data = PatientListResponseDTO(total=total, page=page, limit=limit, items=paginated_items)
    return {
        "success": True,
        "message": "Patients listed successfully",
        "data": data.model_dump()
    }

@router.get("/patients/{patient_id}", status_code=status.HTTP_200_OK)
async def get_patient(
    patient_id: str,
    tenant_id: str = Depends(get_tenant_header)
):
    patient = _patients_store.get(patient_id)
    if not patient or patient.get("tenant_id") != tenant_id:
        raise NotFoundException(message="Patient not found.")
    return {
        "success": True,
        "message": "Patient details retrieved successfully",
        "data": patient
    }

@router.put("/patients/{patient_id}", status_code=status.HTTP_200_OK)
async def update_patient(
    patient_id: str,
    dto: PatientUpdateDTO,
    tenant_id: str = Depends(get_tenant_header)
):
    patient = _patients_store.get(patient_id)
    if not patient or patient.get("tenant_id") != tenant_id:
        raise NotFoundException(message="Patient not found.")
    
    if dto.first_name: patient["first_name"] = dto.first_name
    if dto.last_name: patient["last_name"] = dto.last_name
    if dto.phone: patient["phone"] = dto.phone
    if dto.email: patient["email"] = dto.email
    
    return {
        "success": True,
        "message": "Patient updated successfully",
        "data": patient
    }

@router.delete("/patients/{patient_id}", status_code=status.HTTP_200_OK)
async def delete_patient(
    patient_id: str,
    tenant_id: str = Depends(get_tenant_header)
):
    patient = _patients_store.get(patient_id)
    if not patient or patient.get("tenant_id") != tenant_id:
        raise NotFoundException(message="Patient not found.")
    del _patients_store[patient_id]
    return {
        "success": True,
        "message": "Patient deleted successfully",
        "data": {}
    }

# ==============================================================================
# CLAIM MANAGEMENT ENDPOINTS
# ==============================================================================

@router.post("/claims/", status_code=status.HTTP_201_CREATED)
async def create_claim(
    dto: ClaimCreateDTO,
    tenant_id: str = Depends(get_tenant_header),
    current_user: dict = Depends(get_current_user)
):
    claim_id = f"clm_{int(time.time())}"
    claim = {
        "id": claim_id,
        "tenant_id": tenant_id,
        "patient_id": dto.patient_id,
        "external_claim_ref": dto.external_claim_ref,
        "amount": dto.amount,
        "status": "INGESTED",
        "assigned_to_user_id": None,
        "assigned_to_user_name": None,
        "tags": dto.tags,
        "comments": [],
        "attachments": [],
        "created_at": str(time.time()),
        "updated_at": str(time.time())
    }
    _claims_store[claim_id] = claim
    _claim_timelines[claim_id] = [
        {
            "id": f"tl_{int(time.time())}",
            "event_type": "CREATED",
            "description": f"Claim {dto.external_claim_ref} created.",
            "performed_by": current_user.get("email", "User"),
            "timestamp": str(time.time())
        }
    ]
    return {
        "success": True,
        "message": "Claim created successfully",
        "data": claim
    }

@router.get("/claims/", status_code=status.HTTP_200_OK)
async def list_claims(
    claim_status: Optional[str] = Query(None, alias="status"),
    patient_id: Optional[str] = Query(None),
    tag: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    sort_by: str = Query("-created_at"),
    tenant_id: str = Depends(get_tenant_header)
):
    results = [c for c in _claims_store.values() if c.get("tenant_id") == tenant_id]
    
    if claim_status:
        results = [c for c in results if c["status"] == claim_status.upper()]
    if patient_id:
        results = [c for c in results if c["patient_id"] == patient_id]
    if tag:
        results = [c for c in results if tag in c.get("tags", [])]
        
    reverse = sort_by.startswith("-")
    field = sort_by.lstrip("-")
    results = sorted(results, key=lambda x: x.get(field, 0), reverse=reverse)
    
    total = len(results)
    start = (page - 1) * limit
    paginated_items = results[start:start + limit]
    
    data = ClaimListResponseDTO(total=total, page=page, limit=limit, items=paginated_items)
    return {
        "success": True,
        "message": "Claims listed successfully",
        "data": data.model_dump()
    }

@router.get("/claims/{claim_id}", status_code=status.HTTP_200_OK)
async def get_claim(
    claim_id: str,
    tenant_id: str = Depends(get_tenant_header)
):
    claim = _claims_store.get(claim_id)
    if not claim or claim.get("tenant_id") != tenant_id:
        raise NotFoundException(message="Claim not found.")
    return {
        "success": True,
        "message": "Claim details retrieved successfully",
        "data": claim
    }

@router.put("/claims/{claim_id}", status_code=status.HTTP_200_OK)
async def update_claim(
    claim_id: str,
    dto: ClaimUpdateDTO,
    tenant_id: str = Depends(get_tenant_header),
    current_user: dict = Depends(get_current_user)
):
    claim = _claims_store.get(claim_id)
    if not claim or claim.get("tenant_id") != tenant_id:
        raise NotFoundException(message="Claim not found.")
    
    if dto.status:
        old_status = claim["status"]
        claim["status"] = dto.status.upper()
        _claim_timelines.setdefault(claim_id, []).append({
            "id": f"tl_{int(time.time())}",
            "event_type": "STATUS_CHANGED",
            "description": f"Status updated from {old_status} to {dto.status.upper()}.",
            "performed_by": current_user.get("email", "User"),
            "timestamp": str(time.time())
        })
    if dto.amount is not None:
        claim["amount"] = dto.amount
    
    claim["updated_at"] = str(time.time())
    return {
        "success": True,
        "message": "Claim updated successfully",
        "data": claim
    }

@router.post("/claims/{claim_id}/assign", status_code=status.HTTP_200_OK)
async def assign_claim(
    claim_id: str,
    dto: ClaimAssignDTO,
    tenant_id: str = Depends(get_tenant_header),
    current_user: dict = Depends(get_current_user)
):
    claim = _claims_store.get(claim_id)
    if not claim or claim.get("tenant_id") != tenant_id:
        raise NotFoundException(message="Claim not found.")
    
    claim["assigned_to_user_id"] = dto.user_id
    claim["assigned_to_user_name"] = dto.user_name
    
    _claim_timelines.setdefault(claim_id, []).append({
        "id": f"tl_{int(time.time())}",
        "event_type": "ASSIGNED",
        "description": f"Claim assigned to {dto.user_name}.",
        "performed_by": current_user.get("email", "User"),
        "timestamp": str(time.time())
    })
    return {
        "success": True,
        "message": "Claim assigned successfully",
        "data": claim
    }

@router.post("/claims/{claim_id}/comments", status_code=status.HTTP_200_OK)
async def add_claim_comment(
    claim_id: str,
    dto: ClaimAddCommentDTO,
    tenant_id: str = Depends(get_tenant_header),
    current_user: dict = Depends(get_current_user)
):
    claim = _claims_store.get(claim_id)
    if not claim or claim.get("tenant_id") != tenant_id:
        raise NotFoundException(message="Claim not found.")
    
    cmt = {
        "id": f"cmt_{int(time.time())}",
        "user_id": current_user.get("user_id", "usr_1"),
        "user_name": current_user.get("email", "User"),
        "comment_text": dto.comment_text,
        "created_at": str(time.time())
    }
    claim.setdefault("comments", []).append(cmt)
    
    _claim_timelines.setdefault(claim_id, []).append({
        "id": f"tl_{int(time.time())}",
        "event_type": "COMMENT_ADDED",
        "description": f"Comment added: '{dto.comment_text[:30]}...'",
        "performed_by": current_user.get("email", "User"),
        "timestamp": str(time.time())
    })
    return {
        "success": True,
        "message": "Claim comment added successfully",
        "data": claim
    }

@router.post("/claims/{claim_id}/tags", status_code=status.HTTP_200_OK)
async def add_claim_tag(
    claim_id: str,
    dto: ClaimAddTagDTO,
    tenant_id: str = Depends(get_tenant_header)
):
    claim = _claims_store.get(claim_id)
    if not claim or claim.get("tenant_id") != tenant_id:
        raise NotFoundException(message="Claim not found.")
    
    if dto.tag not in claim.setdefault("tags", []):
        claim["tags"].append(dto.tag)
    return {
        "success": True,
        "message": "Tag added to claim successfully",
        "data": claim
    }

@router.post("/claims/{claim_id}/attachments", status_code=status.HTTP_200_OK)
async def attach_document_to_claim(
    claim_id: str,
    dto: ClaimAttachDocumentDTO,
    tenant_id: str = Depends(get_tenant_header)
):
    claim = _claims_store.get(claim_id)
    if not claim or claim.get("tenant_id") != tenant_id:
        raise NotFoundException(message="Claim not found.")
    
    attachment = {
        "document_id": dto.document_id,
        "file_name": dto.file_name,
        "file_type": dto.file_type,
        "attached_at": str(time.time())
    }
    claim.setdefault("attachments", []).append(attachment)
    return {
        "success": True,
        "message": "Document attached to claim successfully",
        "data": claim
    }

@router.get("/claims/{claim_id}/timeline", status_code=status.HTTP_200_OK)
async def get_claim_timeline(
    claim_id: str,
    tenant_id: str = Depends(get_tenant_header)
):
    claim = _claims_store.get(claim_id)
    if not claim or claim.get("tenant_id") != tenant_id:
        raise NotFoundException(message="Claim not found.")
    timeline = _claim_timelines.get(claim_id, [])
    return {
        "success": True,
        "message": "Claim timeline retrieved successfully",
        "data": timeline
    }
