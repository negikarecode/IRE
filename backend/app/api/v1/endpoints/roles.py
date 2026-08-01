from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel, ConfigDict
from typing import List
from app.core.database import get_db
from app.core.dependencies import get_tenant_header
from app.infrastructure.db.models.user import RoleModel

router = APIRouter()

class RoleCreate(BaseModel):
    name: str
    description: str

class RoleResponse(BaseModel):
    id: str
    tenant_id: str
    name: str
    description: str
    model_config = ConfigDict(from_attributes=True)

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_role(
    role_in: RoleCreate,
    tenant_id: str = Depends(get_tenant_header),
    db: AsyncSession = Depends(get_db)
):
    role = RoleModel(tenant_id=tenant_id, name=role_in.name, description=role_in.description)
    db.add(role)
    await db.commit()
    await db.refresh(role)
    role_data = RoleResponse.model_validate(role)
    return {
        "success": True,
        "message": "Role created successfully",
        "data": role_data.model_dump()
    }

@router.get("/", status_code=status.HTTP_200_OK)
async def list_roles(
    tenant_id: str = Depends(get_tenant_header),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(RoleModel).where(RoleModel.tenant_id == tenant_id))
    roles = result.scalars().all()
    roles_data = [RoleResponse.model_validate(r).model_dump() for r in roles]
    return {
        "success": True,
        "message": "Roles retrieved successfully",
        "data": roles_data
    }
