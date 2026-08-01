from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime

class HospitalCreate(BaseModel):
    name: str
    npi_number: Optional[str] = None
    address: Optional[Dict[str, Any]] = None

class HospitalResponse(BaseModel):
    id: str
    tenant_id: str
    name: str
    npi_number: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class PatientCreate(BaseModel):
    first_name: str
    last_name: str
    dob: Optional[str] = None
    medical_record_number: str
    hospital_id: Optional[str] = None

class PatientResponse(BaseModel):
    id: str
    tenant_id: str
    first_name: str
    last_name: str
    medical_record_number: str
    created_at: datetime

    class Config:
        from_attributes = True

class ClaimCreate(BaseModel):
    patient_id: str
    hospital_id: Optional[str] = None
    external_claim_ref: str
    amount: float
    raw_payload: Dict[str, Any]

class ClaimResponse(BaseModel):
    id: str
    tenant_id: str
    patient_id: str
    external_claim_ref: str
    status: str
    amount: float
    raw_payload: Dict[str, Any]
    adjudication_output: Optional[Dict[str, Any]]
    created_at: datetime

    class Config:
        from_attributes = True

class DocumentResponse(BaseModel):
    id: str
    tenant_id: str
    file_name: str
    file_path: str
    content_type: str
    created_at: datetime

    class Config:
        from_attributes = True

class AuditLogResponse(BaseModel):
    id: str
    tenant_id: str
    actor_id: str
    action: str
    resource: str
    resource_id: str
    details: Optional[Dict[str, Any]]
    created_at: datetime

    class Config:
        from_attributes = True

class NotificationCreate(BaseModel):
    user_id: str
    title: str
    message: str

class NotificationResponse(BaseModel):
    id: str
    tenant_id: str
    user_id: str
    title: str
    message: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True

class SettingCreate(BaseModel):
    key: str
    value: Dict[str, Any]

class SettingResponse(BaseModel):
    id: str
    tenant_id: str
    key: str
    value: Dict[str, Any]

    class Config:
        from_attributes = True
