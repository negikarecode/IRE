from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from app.core.database import get_db
from app.core.dependencies import get_tenant_header
from app.application.schemas.domain_schemas import HospitalCreate, HospitalResponse
from app.infrastructure.db.models.hospital import HospitalModel

router = APIRouter()

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_hospital(
    hospital_in: HospitalCreate,
    tenant_id: str = Depends(get_tenant_header),
    db: AsyncSession = Depends(get_db)
):
    hospital = HospitalModel(
        tenant_id=tenant_id,
        name=hospital_in.name,
        npi_number=hospital_in.npi_number,
        address=hospital_in.address
    )
    db.add(hospital)
    await db.commit()
    await db.refresh(hospital)
    hosp_data = HospitalResponse.model_validate(hospital)
    return {
        "success": True,
        "message": "Hospital created successfully",
        "data": hosp_data.model_dump()
    }

@router.get("/", status_code=status.HTTP_200_OK)
async def list_hospitals(
    tenant_id: str = Depends(get_tenant_header),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(HospitalModel).where(HospitalModel.tenant_id == tenant_id))
    hospitals = result.scalars().all()
    data = [HospitalResponse.model_validate(h).model_dump() for h in hospitals]
    return {
        "success": True,
        "message": "Hospitals retrieved successfully",
        "data": data
    }
