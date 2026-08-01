from fastapi import APIRouter, Depends, status
from typing import List
from app.application.schemas.auth import OrganizationCreateDTO, OrganizationResponseDTO
from app.core.dependencies import get_current_user, RequireRole
import time

router = APIRouter()

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_organization(
    dto: OrganizationCreateDTO,
    current_user: dict = Depends(RequireRole(["ADMIN", "SUPER_ADMIN"]))
):
    """
    Create Organization Hierarchy Node (RBAC Protected).
    """
    org_id = f"org_{int(time.time())}"
    org = OrganizationResponseDTO(
        id=org_id,
        tenant_id=current_user.get("tenant_id"),
        hospital_id=current_user.get("hospital_id", "hosp_01"),
        name=dto.name,
        org_type=dto.org_type,
        created_at=str(time.time())
    )
    return {
        "success": True,
        "message": "Organization created successfully",
        "data": org.model_dump()
    }

@router.get("/", status_code=status.HTTP_200_OK)
async def list_organizations(current_user: dict = Depends(get_current_user)):
    """
    List Tenant Organizations.
    """
    orgs = [
        OrganizationResponseDTO(
            id="org_default",
            tenant_id=current_user.get("tenant_id"),
            hospital_id=current_user.get("hospital_id", "hosp_01"),
            name="Main Hospital System",
            org_type="HOSPITAL_GROUP",
            created_at=str(time.time())
        )
    ]
    return {
        "success": True,
        "message": "Organizations listed successfully",
        "data": [o.model_dump() for o in orgs]
    }
