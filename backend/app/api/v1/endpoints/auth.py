import logging
import traceback
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, HTTPException, status, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import Optional
from pydantic import BaseModel, EmailStr, Field

from app.core.database import get_db
from app.application.schemas.auth import (
    HospitalRegisterDTO, LoginDTO, TokenResponseDTO, RefreshTokenDTO,
    PasswordResetRequestDTO, PasswordResetConfirmDTO, UserMeResponseDTO
)
from app.core.security import (
    get_password_hash, verify_password, create_access_token,
    create_refresh_token, decode_token
)
from app.infrastructure.db.models.auth_models import (
    HospitalModel, OrganizationModel, UserModel, RoleModel, SessionModel
)
from app.config import settings

# Configure Structured Auth Logger
logger = logging.getLogger("auth_logger")
logging.basicConfig(level=logging.INFO)

router = APIRouter()

# Frontend-compatible signup DTO
class FrontendSignupDTO(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str
    hospital_name: str


class ErrorResponseDTO(BaseModel):
    success: bool = False
    error: str
    message: str

async def create_default_hospital_roles(session: AsyncSession, hospital_id: str):
    roles = [
        {"name": "Hospital Admin", "description": "Full administrative access to hospital settings and users"},
        {"name": "Billing Executive", "description": "Manage claims, submissions, coding fixes, and revenue recovery"},
        {"name": "Reviewer", "description": "Review AI findings, clinical documentation, and approve claim line items"}
    ]
    created_roles = []
    for r in roles:
        role_obj = RoleModel(
            hospital_id=hospital_id,
            name=r["name"],
            description=r["description"]
        )
        session.add(role_obj)
        created_roles.append(role_obj)
    await session.flush()
    return created_roles

from app.core.exceptions import ConflictException, UnauthorizedException, NotFoundException

@router.post("/register", status_code=status.HTTP_201_CREATED)
@router.post("/hospitals/register", status_code=status.HTTP_201_CREATED)
async def register_hospital(dto: HospitalRegisterDTO, db: AsyncSession = Depends(get_db)):
    """
    Hospital Registration Endpoint.
    Creates Hospital, Organization, 3 Default Hospital Roles, Admin User, and Session in a single atomic database transaction.
    """
    logger.info(f"[AUTH_REGISTER_START] Attempting registration for Hospital: '{dto.hospital_name}', Email: '{dto.email}'")

    # Check if user already exists
    existing_user_stmt = select(UserModel).where(UserModel.email == dto.email)
    existing_user_result = await db.execute(existing_user_stmt)
    if existing_user_result.scalar_one_or_none():
        logger.warning(f"[AUTH_REGISTER_FAILED] Email '{dto.email}' already exists.")
        raise ConflictException(message=f"User with email '{dto.email}' is already registered.")

    try:
        # Single Database Transaction
        # 1. Create Hospital
        hospital = HospitalModel(
            name=dto.hospital_name,
            facility_type=dto.facility_type,
            npi_number=dto.npi_number
        )
        db.add(hospital)
        await db.flush()

        # 2. Create First Organization
        organization = OrganizationModel(
            hospital_id=hospital.id,
            name=f"{dto.hospital_name} Group"
        )
        db.add(organization)
        await db.flush()

        # 3. Create Default Hospital Roles
        roles = await create_default_hospital_roles(db, hospital.id)
        admin_role = roles[0] # Hospital Admin

        # 4. Create Admin User with Bcrypt Password Hash
        hashed_pw = get_password_hash(dto.password)
        admin_user = UserModel(
            hospital_id=hospital.id,
            organization_id=organization.id,
            email=dto.email,
            hashed_password=hashed_pw,
            full_name=dto.admin_full_name or "Hospital Administrator"
        )
        admin_user.roles.append(admin_role)
        db.add(admin_user)
        await db.flush()

        # 5. Issue JWT Access & Refresh Tokens
        token_payload = {
            "sub": admin_user.id,
            "email": admin_user.email,
            "hospital_id": hospital.id,
            "hospital_name": hospital.name,
            "roles": [r.name for r in admin_user.roles]
        }
        access_token = create_access_token(token_payload)
        refresh_token = create_refresh_token({"sub": admin_user.id, "email": admin_user.email})

        session_obj = SessionModel(
            user_id=admin_user.id,
            token=access_token,
            refresh_token=refresh_token,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        db.add(session_obj)

        # Commit single atomic transaction
        await db.commit()
        logger.info(f"[AUTH_REGISTER_SUCCESS] Hospital '{hospital.name}' (ID: {hospital.id}) registered successfully with Admin: '{admin_user.email}'")

        token_data = TokenResponseDTO(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user_id=admin_user.id,
            hospital_id=hospital.id,
            hospital_name=hospital.name,
            roles=[r.name for r in admin_user.roles]
        )
        return {
            "success": True,
            "message": "Hospital registered successfully",
            "data": token_data.model_dump()
        }
    except ConflictException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"[AUTH_REGISTER_ERROR] Registration transaction failed: {str(e)}\nStack trace: {traceback.format_exc()}")
        raise Exception(f"An unexpected error occurred during registration: {str(e)}")

@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup_frontend(dto: FrontendSignupDTO, db: AsyncSession = Depends(get_db)):
    """
    Frontend-compatible Signup Endpoint.
    Accepts simplified format from frontend and maps to internal registration logic.
    """
    logger.info(f"[AUTH_SIGNUP_START] Attempting signup for Hospital: '{dto.hospital_name}', Email: '{dto.email}'")

    # Check if user already exists
    existing_user_stmt = select(UserModel).where(UserModel.email == dto.email)
    existing_user_result = await db.execute(existing_user_stmt)
    if existing_user_result.scalar_one_or_none():
        logger.warning(f"[AUTH_SIGNUP_FAILED] Email '{dto.email}' already exists.")
        raise ConflictException(message=f"User with email '{dto.email}' is already registered.")

    try:
        # Single Database Transaction
        # 1. Create Hospital
        hospital = HospitalModel(
            name=dto.hospital_name,
            facility_type="Inpatient Hospital",
            npi_number=None
        )
        db.add(hospital)
        await db.flush()

        # 2. Create First Organization
        organization = OrganizationModel(
            hospital_id=hospital.id,
            name=f"{dto.hospital_name} Group"
        )
        db.add(organization)
        await db.flush()

        # 3. Create Default Hospital Roles
        roles = await create_default_hospital_roles(db, hospital.id)
        admin_role = roles[0] # Hospital Admin

        # 4. Create Admin User with Bcrypt Password Hash
        hashed_pw = get_password_hash(dto.password)
        admin_user = UserModel(
            hospital_id=hospital.id,
            organization_id=organization.id,
            email=dto.email,
            hashed_password=hashed_pw,
            full_name=dto.full_name
        )
        admin_user.roles.append(admin_role)
        db.add(admin_user)
        await db.flush()

        # 5. Issue JWT Access & Refresh Tokens
        token_payload = {
            "sub": admin_user.id,
            "email": admin_user.email,
            "hospital_id": hospital.id,
            "hospital_name": hospital.name,
            "roles": [r.name for r in admin_user.roles]
        }
        access_token = create_access_token(token_payload)
        refresh_token = create_refresh_token({"sub": admin_user.id, "email": admin_user.email})

        session_obj = SessionModel(
            user_id=admin_user.id,
            token=access_token,
            refresh_token=refresh_token,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        db.add(session_obj)

        # Commit single atomic transaction
        await db.commit()
        logger.info(f"[AUTH_SIGNUP_SUCCESS] Hospital '{hospital.name}' (ID: {hospital.id}) registered successfully with Admin: '{admin_user.email}'")

        token_data = TokenResponseDTO(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user_id=admin_user.id,
            hospital_id=hospital.id,
            hospital_name=hospital.name,
            roles=[r.name for r in admin_user.roles]
        )
        return {
            "success": True,
            "message": "User signed up successfully",
            "data": token_data.model_dump()
        }
    except ConflictException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"[AUTH_SIGNUP_ERROR] Signup transaction failed: {str(e)}\nStack trace: {traceback.format_exc()}")
        raise Exception(f"An unexpected error occurred during signup: {str(e)}")


@router.post("/login", status_code=status.HTTP_200_OK)
@router.post("/hospitals/login", status_code=status.HTTP_200_OK)
async def login_hospital(dto: LoginDTO, db: AsyncSession = Depends(get_db)):
    """
    Hospital User Login Endpoint.
    Authenticates user from database and issues JWT Access & Refresh Tokens.
    """
    logger.info(f"[AUTH_LOGIN_ATTEMPT] Email: '{dto.email}'")

    stmt = select(UserModel).options(selectinload(UserModel.roles)).where(UserModel.email == dto.email)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()

    if not user or not verify_password(dto.password, user.hashed_password):
        logger.warning(f"[AUTH_LOGIN_FAILED] Invalid credentials for email: '{dto.email}'")
        raise UnauthorizedException(message="Incorrect email or password")

    # Fetch Hospital
    hospital_stmt = select(HospitalModel).where(HospitalModel.id == user.hospital_id)
    hosp_res = await db.execute(hospital_stmt)
    hospital = hosp_res.scalar_one_or_none()
    hosp_name = hospital.name if hospital else "Metro General Hospital"

    expires_minutes = (60 * 24 * 30) if dto.remember_me else settings.ACCESS_TOKEN_EXPIRE_MINUTES
    token_payload = {
        "sub": user.id,
        "email": user.email,
        "hospital_id": user.hospital_id,
        "hospital_name": hosp_name,
        "roles": [r.name for r in user.roles]
    }
    access_token = create_access_token(token_payload)
    refresh_token = create_refresh_token({"sub": user.id, "email": user.email})

    session_obj = SessionModel(
        user_id=user.id,
        token=access_token,
        refresh_token=refresh_token,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    )
    db.add(session_obj)
    await db.commit()

    logger.info(f"[AUTH_LOGIN_SUCCESS] User '{user.email}' logged in successfully.")
    token_data = TokenResponseDTO(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=expires_minutes * 60,
        user_id=user.id,
        hospital_id=user.hospital_id,
        hospital_name=hosp_name,
        roles=[r.name for r in user.roles]
    )
    return {
        "success": True,
        "message": "Login successful",
        "data": token_data.model_dump()
    }

@router.get("/me", status_code=status.HTTP_200_OK)
async def get_current_user_profile(authorization: Optional[str] = Header(None), db: AsyncSession = Depends(get_db)):
    """
    Get Current Authenticated User Session Profile.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise UnauthorizedException(message="Missing or invalid Bearer token")

    token = authorization.split(" ")[1]
    payload = decode_token(token)
    if not payload:
        raise UnauthorizedException(message="Invalid or expired access token")

    user_id = payload.get("sub")
    stmt = select(UserModel).options(selectinload(UserModel.roles)).where(UserModel.id == user_id)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()
    if not user:
        raise NotFoundException(message="User session not found")

    hospital_stmt = select(HospitalModel).where(HospitalModel.id == user.hospital_id)
    hosp_res = await db.execute(hospital_stmt)
    hospital = hosp_res.scalar_one_or_none()
    hosp_name = hospital.name if hospital else "Metro General Hospital"

    user_me = UserMeResponseDTO(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        hospital_id=user.hospital_id,
        hospital_name=hosp_name,
        organization_id=user.organization_id,
        roles=[r.name for r in user.roles],
        is_active=user.is_active
    )
    return {
        "success": True,
        "message": "User session profile retrieved successfully",
        "data": user_me.model_dump()
    }

@router.post("/refresh", status_code=status.HTTP_200_OK)
async def refresh_tokens(dto: RefreshTokenDTO, db: AsyncSession = Depends(get_db)):
    """
    Refresh Token Endpoint.
    Validates Refresh Token against Database, revokes old session, and issues new pair.
    """
    payload = decode_token(dto.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise UnauthorizedException(message="Invalid or expired refresh token")

    # Check if session exists in DB (enforce session validation and revocation check)
    session_stmt = select(SessionModel).where(SessionModel.refresh_token == dto.refresh_token)
    session_res = await db.execute(session_stmt)
    old_session = session_res.scalar_one_or_none()
    if not old_session:
        raise UnauthorizedException(message="Refresh token has been revoked or is invalid")

    user_id = payload.get("sub")
    stmt = select(UserModel).options(selectinload(UserModel.roles)).where(UserModel.id == user_id)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()
    if not user:
        raise NotFoundException(message="User not found")

    # Delete old session (Token Rotation)
    await db.delete(old_session)

    hospital_stmt = select(HospitalModel).where(HospitalModel.id == user.hospital_id)
    hosp_res = await db.execute(hospital_stmt)
    hospital = hosp_res.scalar_one_or_none()
    hosp_name = hospital.name if hospital else "Metro General Hospital"

    token_payload = {
        "sub": user.id,
        "email": user.email,
        "hospital_id": user.hospital_id,
        "hospital_name": hosp_name,
        "roles": [r.name for r in user.roles]
    }
    new_access_token = create_access_token(token_payload)
    new_refresh_token = create_refresh_token({"sub": user.id, "email": user.email})

    session_obj = SessionModel(
        user_id=user.id,
        token=new_access_token,
        refresh_token=new_refresh_token,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    db.add(session_obj)
    await db.commit()

    token_data = TokenResponseDTO(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user_id=user.id,
        hospital_id=user.hospital_id,
        hospital_name=hosp_name,
        roles=[r.name for r in user.roles]
    )
    return {
        "success": True,
        "message": "Tokens refreshed successfully",
        "data": token_data.model_dump()
    }

@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(authorization: Optional[str] = Header(None), db: AsyncSession = Depends(get_db)):
    """
    Logout Endpoint. Revokes user session.
    """
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        stmt = select(SessionModel).where(SessionModel.token == token)
        res = await db.execute(stmt)
        session_obj = res.scalar_one_or_none()
        if session_obj:
            await db.delete(session_obj)
            await db.commit()
    return {
        "success": True,
        "message": "Logged out successfully",
        "data": {"status": "LOGGED_OUT_SUCCESSFULLY"}
    }
