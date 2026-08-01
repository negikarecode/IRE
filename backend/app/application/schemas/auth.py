from pydantic import BaseModel, EmailStr, Field, model_validator
from typing import List, Optional

class HospitalRegisterDTO(BaseModel):
    hospital_name: str = Field(..., example="Metro General Hospital")
    facility_type: str = Field(default="Inpatient Hospital", example="Inpatient Hospital")
    npi_number: Optional[str] = Field(default=None, example="1982736450")
    email: EmailStr = Field(..., example="admin@metrohospital.org")
    password: str = Field(..., min_length=6, example="SuperSecurePass123!")
    confirm_password: Optional[str] = Field(default=None, example="SuperSecurePass123!")
    admin_full_name: Optional[str] = Field(default="Hospital Administrator", example="Dr. Sarah Jenkins")

    @model_validator(mode="after")
    def validate_passwords_match(self):
        if self.confirm_password and self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self

class LoginDTO(BaseModel):
    email: EmailStr = Field(..., example="admin@metrohospital.org")
    password: str = Field(..., example="SuperSecurePass123!")
    remember_me: Optional[bool] = Field(default=False)

class TokenResponseDTO(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: str
    hospital_id: str
    hospital_name: str
    roles: List[str]

class UserMeResponseDTO(BaseModel):
    id: str
    email: str
    full_name: str
    hospital_id: str
    hospital_name: str
    organization_id: Optional[str] = None
    roles: List[str]
    is_active: bool = True

class RefreshTokenDTO(BaseModel):
    refresh_token: str

class PasswordResetRequestDTO(BaseModel):
    email: EmailStr

class PasswordResetConfirmDTO(BaseModel):
    reset_token: str
    new_password: str = Field(..., min_length=6)

class UserCreateDTO(BaseModel):
    email: EmailStr
    full_name: str
    password: str = Field(..., min_length=6)
    roles: List[str] = ["Billing Executive"]

class UserProfileDTO(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    tenant_id: Optional[str] = None
    hospital_id: str
    roles: List[str]
    is_active: bool

class OrganizationCreateDTO(BaseModel):
    name: str
    org_type: str = "HOSPITAL_GROUP"

class OrganizationResponseDTO(BaseModel):
    id: str
    tenant_id: Optional[str] = None
    hospital_id: Optional[str] = None
    name: str
    org_type: str = "HOSPITAL_GROUP"
    created_at: Optional[str] = None

class TenantCreate(BaseModel):
    name: str
    slug: str
    isolation_strategy: str = "ROW_LEVEL"

class TenantResponse(BaseModel):
    id: str
    name: str
    slug: str
    is_active: bool = True
