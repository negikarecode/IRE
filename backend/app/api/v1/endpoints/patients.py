from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from app.core.database import get_db
from app.core.dependencies import get_tenant_header
from app.application.schemas.domain_schemas import PatientCreate, PatientResponse
from app.infrastructure.db.models.hospital import PatientModel

router = APIRouter()

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_patient(
    patient_in: PatientCreate,
    tenant_id: str = Depends(get_tenant_header),
    db: AsyncSession = Depends(get_db)
):
    patient = PatientModel(
        tenant_id=tenant_id,
        hospital_id=patient_in.hospital_id,
        first_name=patient_in.first_name,
        last_name=patient_in.last_name,
        dob=patient_in.dob,
        medical_record_number=patient_in.medical_record_number
    )
    db.add(patient)
    await db.commit()
    await db.refresh(patient)
    pat_data = PatientResponse.model_validate(patient)
    return {
        "success": True,
        "message": "Patient created successfully",
        "data": pat_data.model_dump()
    }

@router.get("/", status_code=status.HTTP_200_OK)
async def list_patients(
    tenant_id: str = Depends(get_tenant_header),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(PatientModel).where(PatientModel.tenant_id == tenant_id))
    patients = result.scalars().all()
    data = [PatientResponse.model_validate(p).model_dump() for p in patients]
    return {
        "success": True,
        "message": "Patients retrieved successfully",
        "data": data
    }
