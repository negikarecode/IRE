from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from app.core.database import get_db
from app.core.exceptions import ConflictException
from app.application.schemas.auth import TenantCreate, TenantResponse
from app.infrastructure.db.models.tenant import TenantModel

router = APIRouter()

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_tenant(tenant_in: TenantCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TenantModel).where(TenantModel.slug == tenant_in.slug))
    if result.scalars().first():
        raise ConflictException(message=f"Tenant slug '{tenant_in.slug}' already exists")
    
    tenant = TenantModel(
        name=tenant_in.name,
        slug=tenant_in.slug,
        isolation_strategy=tenant_in.isolation_strategy
    )
    db.add(tenant)
    await db.commit()
    await db.refresh(tenant)
    
    data = TenantResponse(
        id=tenant.id,
        name=tenant.name,
        slug=tenant.slug,
        is_active=tenant.is_active
    )
    return {
        "success": True,
        "message": "Tenant created successfully",
        "data": data.model_dump()
    }

@router.get("/", status_code=status.HTTP_200_OK)
async def list_tenants(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TenantModel))
    tenants = result.scalars().all()
    data = [
        TenantResponse(
            id=t.id,
            name=t.name,
            slug=t.slug,
            is_active=t.is_active
        ).model_dump()
        for t in tenants
    ]
    return {
        "success": True,
        "message": "Tenants retrieved successfully",
        "data": data
    }
