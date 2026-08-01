from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from app.core.database import get_db
from app.core.dependencies import get_tenant_header
from app.application.schemas.domain_schemas import SettingCreate, SettingResponse
from app.infrastructure.db.models.audit_log import SettingModel

router = APIRouter()

@router.post("/", status_code=status.HTTP_200_OK)
async def update_setting(
    setting_in: SettingCreate,
    tenant_id: str = Depends(get_tenant_header),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(SettingModel).where(
            SettingModel.tenant_id == tenant_id,
            SettingModel.key == setting_in.key
        )
    )
    setting = result.scalars().first()
    if setting:
        setting.value = setting_in.value
    else:
        setting = SettingModel(tenant_id=tenant_id, key=setting_in.key, value=setting_in.value)
        db.add(setting)

    await db.commit()
    await db.refresh(setting)
    data = SettingResponse.model_validate(setting)
    return {
        "success": True,
        "message": "Setting updated successfully",
        "data": data.model_dump()
    }

@router.get("/", status_code=status.HTTP_200_OK)
async def get_settings(
    tenant_id: str = Depends(get_tenant_header),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(SettingModel).where(SettingModel.tenant_id == tenant_id))
    settings_list = result.scalars().all()
    data = [SettingResponse.model_validate(s).model_dump() for s in settings_list]
    return {
        "success": True,
        "message": "Settings retrieved successfully",
        "data": data
    }
