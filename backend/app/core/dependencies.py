from fastapi import Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer
from app.core.security import decode_token
from typing import List, Optional

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/hospitals/login")

async def get_tenant_header(x_tenant_id: Optional[str] = Header(None)) -> str:
    if not x_tenant_id:
        return "tenant_default"
    return x_tenant_id

async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {
        "user_id": payload.get("sub"),
        "email": payload.get("email"),
        "tenant_id": payload.get("tenant_id"),
        "roles": payload.get("roles", []),
        "permissions": payload.get("permissions", [])
    }

class RequireRole:
    """
    Role-Based Access Control (RBAC) Dependency.
    """
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: dict = Depends(get_current_user)) -> dict:
        user_roles = current_user.get("roles", [])
        if not any(role in user_roles for role in self.allowed_roles) and "SUPER_ADMIN" not in user_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User requires one of roles: {self.allowed_roles}"
            )
        return current_user

class RequirePermission:
    """
    Granular Permission Dependency.
    """
    def __init__(self, required_permission: str):
        self.required_permission = required_permission

    def __call__(self, current_user: dict = Depends(get_current_user)) -> dict:
        user_perms = current_user.get("permissions", [])
        user_roles = current_user.get("roles", [])
        if self.required_permission not in user_perms and "SUPER_ADMIN" not in user_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{self.required_permission}' is required"
            )
        return current_user
