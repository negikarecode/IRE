import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Boolean, JSON
from app.core.database import Base
from app.infrastructure.db.models.auth_models import HospitalModel, OrganizationModel

from sqlalchemy import Index

class PatientModel(Base):
    __tablename__ = "patients"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(64), nullable=False, index=True)
    hospital_id = Column(String(64), nullable=True, index=True)
    first_name = Column(String(128), nullable=False)
    last_name = Column(String(128), nullable=False)
    dob = Column(String(32), nullable=True)
    medical_record_number = Column(String(128), nullable=False, index=True)
    
    # Soft deletes and audit timestamps
    is_deleted = Column(Boolean, default=False, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_patients_tenant_mrn", "tenant_id", "medical_record_number"),
        Index("idx_patients_hospital_mrn", "hospital_id", "medical_record_number"),
    )
