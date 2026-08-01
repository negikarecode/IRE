from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional
from app.core.database import get_db
from app.core.dependencies import get_tenant_header
from app.application.schemas.domain_schemas import AuditLogResponse
from app.infrastructure.db.models.audit_log import AuditLogModel

router = APIRouter()

@router.get("/", status_code=status.HTTP_200_OK)
async def get_audit_logs(
    resource: Optional[str] = None,
    tenant_id: str = Depends(get_tenant_header),
    db: AsyncSession = Depends(get_db)
):
    query = select(AuditLogModel).where(AuditLogModel.tenant_id == tenant_id)
    if resource:
        query = query.where(AuditLogModel.resource == resource)
    result = await db.execute(query)
    logs = result.scalars().all()
    data = [AuditLogResponse.model_validate(log).model_dump() for log in logs]
    return {
        "success": True,
        "message": "Audit logs retrieved successfully",
        "data": data
    }
