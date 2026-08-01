from fastapi import APIRouter, Depends, status
from typing import List
from pydantic import BaseModel, Field
from app.application.schemas.auth import UserCreateDTO, UserProfileDTO
from app.core.dependencies import get_current_user, RequireRole
import time

router = APIRouter()

class ProfileUpdateDTO(BaseModel):
    full_name: str = Field(..., example="Dr. Sarah Jenkins")

@router.get("/me", status_code=status.HTTP_200_OK)
async def get_my_profile(current_user: dict = Depends(get_current_user)):
    """
    Get Current Authenticated User Profile.
    """
    profile = UserProfileDTO(
        id=current_user.get("user_id", "usr_me"),
        email=current_user.get("email", "admin@hospital.org"),
        full_name="Hospital Administrator",
        tenant_id=current_user.get("tenant_id"),
        hospital_id=current_user.get("hospital_id", "hosp_01"),
        roles=current_user.get("roles", ["Hospital Admin"]),
        is_active=True
    )
    return {
        "success": True,
        "message": "User profile retrieved successfully",
        "data": profile.model_dump()
    }

@router.put("/me", status_code=status.HTTP_200_OK)
async def update_my_profile(
    dto: ProfileUpdateDTO,
    current_user: dict = Depends(get_current_user)
):
    """
    Update Current Authenticated User Profile.
    """
    profile = UserProfileDTO(
        id=current_user.get("user_id", "usr_me"),
        email=current_user.get("email", "admin@hospital.org"),
        full_name=dto.full_name,
        tenant_id=current_user.get("tenant_id"),
        hospital_id=current_user.get("hospital_id", "hosp_01"),
        roles=current_user.get("roles", ["Hospital Admin"]),
        is_active=True
    )
    return {
        "success": True,
        "message": "User profile updated successfully",
        "data": profile.model_dump()
    }

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user(
    dto: UserCreateDTO,
    current_user: dict = Depends(RequireRole(["ADMIN", "HOSPITAL_ADMIN"]))
):
    """
    Create User under Tenant (RBAC protected).
    """
    new_id = f"usr_{int(time.time())}"
    user = UserProfileDTO(
        id=new_id,
        email=dto.email,
        full_name=dto.full_name,
        tenant_id=current_user.get("tenant_id"),
        hospital_id=current_user.get("hospital_id", "hosp_01"),
        roles=dto.roles,
        is_active=True
    )
    return {
        "success": True,
        "message": "User created successfully",
        "data": user.model_dump()
    }

@router.get("/", status_code=status.HTTP_200_OK)
async def list_users(current_user: dict = Depends(RequireRole(["ADMIN", "HOSPITAL_ADMIN"]))):
    """
    List Users under Tenant (RBAC protected).
    """
    users_list = [
        UserProfileDTO(
            id=current_user.get("user_id", "usr_me"),
            email=current_user.get("email", "admin@hospital.org"),
            full_name="Hospital Administrator",
            tenant_id=current_user.get("tenant_id"),
            hospital_id=current_user.get("hospital_id", "hosp_01"),
            roles=current_user.get("roles", ["Hospital Admin"]),
            is_active=True
        )
    ]
    return {
        "success": True,
        "message": "Users listed successfully",
        "data": [u.model_dump() for u in users_list]
    }
