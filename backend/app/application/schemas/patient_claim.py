from pydantic import BaseModel, Field
from typing import List, Optional, Any
from datetime import datetime

# ==========================================
# Patient Schemas
# ==========================================
class PatientCreateDTO(BaseModel):
    mrn: str = Field(..., example="MRN-90214")
    first_name: str = Field(..., example="Jane")
    last_name: str = Field(..., example="Doe")
    dob: str = Field(..., example="1985-04-12")
    gender: Optional[str] = Field(default="FEMALE", example="FEMALE")
    phone: Optional[str] = Field(default="+1-555-0192", example="+1-555-0192")
    email: Optional[str] = Field(default="jane.doe@example.com", example="jane.doe@example.com")
    hospital_id: Optional[str] = Field(default="hosp_01", example="hosp_01")

class PatientUpdateDTO(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None

class PatientResponseDTO(BaseModel):
    id: str
    tenant_id: str
    mrn: str
    first_name: str
    last_name: str
    dob: str
    gender: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    hospital_id: Optional[str] = None
    created_at: str

class PatientListResponseDTO(BaseModel):
    total: int
    page: int
    limit: int
    items: List[PatientResponseDTO]

# ==========================================
# Claim Schemas
# ==========================================
class ClaimCommentDTO(BaseModel):
    id: str
    user_id: str
    user_name: str
    comment_text: str
    created_at: str

class ClaimTimelineEventDTO(BaseModel):
    id: str
    event_type: str  # CREATED, STATUS_CHANGED, ASSIGNED, COMMENT_ADDED, TAG_ADDED, ATTACHMENT_ADDED
    description: str
    performed_by: str
    timestamp: str

class ClaimAttachmentDTO(BaseModel):
    document_id: str
    file_name: str
    file_type: str
    attached_at: str

class ClaimCreateDTO(BaseModel):
    patient_id: str = Field(..., example="pat_9001")
    external_claim_ref: str = Field(..., example="CLM-900123")
    amount: float = Field(..., example=2450.00)
    service_date: Optional[str] = Field(default="2026-07-31", example="2026-07-31")
    tags: List[str] = Field(default_factory=list, example=["URGENT", "OUTPATIENT"])

class ClaimUpdateDTO(BaseModel):
    status: Optional[str] = None
    amount: Optional[float] = None
    assigned_to_user_id: Optional[str] = None

class ClaimAssignDTO(BaseModel):
    user_id: str
    user_name: str

class ClaimAddCommentDTO(BaseModel):
    comment_text: str

class ClaimAddTagDTO(BaseModel):
    tag: str

class ClaimAttachDocumentDTO(BaseModel):
    document_id: str
    file_name: str
    file_type: str

class ClaimResponseDTO(BaseModel):
    id: str
    tenant_id: str
    patient_id: str
    external_claim_ref: str
    amount: float
    status: str  # INGESTED, IN_REASONING, ADJUDICATED, ESCALATED_HITL, APPROVED, DENIED
    assigned_to_user_id: Optional[str] = None
    assigned_to_user_name: Optional[str] = None
    tags: List[str] = []
    comments: List[ClaimCommentDTO] = []
    attachments: List[ClaimAttachmentDTO] = []
    created_at: str
    updated_at: str

class ClaimListResponseDTO(BaseModel):
    total: int
    page: int
    limit: int
    items: List[ClaimResponseDTO]
