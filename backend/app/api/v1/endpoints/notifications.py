from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from app.core.database import get_db
from app.core.dependencies import get_tenant_header
from app.application.schemas.domain_schemas import NotificationCreate, NotificationResponse
from app.infrastructure.db.models.audit_log import NotificationModel
from app.infrastructure.tasks.background_jobs import send_async_notification

router = APIRouter()

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_notification(
    notification_in: NotificationCreate,
    tenant_id: str = Depends(get_tenant_header),
    db: AsyncSession = Depends(get_db)
):
    notif = NotificationModel(
        tenant_id=tenant_id,
        user_id=notification_in.user_id,
        title=notification_in.title,
        message=notification_in.message
    )
    db.add(notif)
    await db.commit()
    await db.refresh(notif)

    # Queue background job
    send_async_notification.delay(tenant_id, notification_in.user_id, notification_in.title, notification_in.message)

    data = NotificationResponse.model_validate(notif)
    return {
        "success": True,
        "message": "Notification created successfully",
        "data": data.model_dump()
    }

@router.get("/", status_code=status.HTTP_200_OK)
async def list_notifications(
    tenant_id: str = Depends(get_tenant_header),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(NotificationModel).where(NotificationModel.tenant_id == tenant_id))
    notifications = result.scalars().all()
    data = [NotificationResponse.model_validate(n).model_dump() for n in notifications]
    return {
        "success": True,
        "message": "Notifications retrieved successfully",
        "data": data
    }
