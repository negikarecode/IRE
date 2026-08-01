from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text
from app.core.database import get_db
from app.core.exceptions import DatabaseException

router = APIRouter()

@router.get("/healthz", status_code=status.HTTP_200_OK)
async def liveness_probe():
    return {
        "success": True,
        "message": "Liveness check passed",
        "data": {
            "status": "ok",
            "service": "IRE Platform API"
        }
    }

@router.get("/readyz", status_code=status.HTTP_200_OK)
async def readiness_probe(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
        return {
            "success": True,
            "message": "Readiness check passed",
            "data": {
                "status": "ready",
                "database": "connected"
            }
        }
    except Exception as e:
        raise DatabaseException(message="Database connectivity check failed", details={"database_error": str(e)})
