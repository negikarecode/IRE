import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Table, Text, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base

user_roles_association = Table(
    "user_roles_association",
    Base.metadata,
    Column("user_id", String(64), ForeignKey("auth_users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", String(64), ForeignKey("auth_roles.id", ondelete="CASCADE"), primary_key=True)
)

class HospitalModel(Base):
    __tablename__ = "auth_hospitals"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    facility_type = Column(String(128), nullable=False, default="Inpatient Hospital")
    npi_number = Column(String(64), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    organizations = relationship("OrganizationModel", back_populates="hospital", cascade="all, delete-orphan")
    users = relationship("UserModel", back_populates="hospital", cascade="all, delete-orphan")
    roles = relationship("RoleModel", back_populates="hospital", cascade="all, delete-orphan")


class OrganizationModel(Base):
    __tablename__ = "auth_organizations"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    hospital_id = Column(String(64), ForeignKey("auth_hospitals.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    created_by = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    hospital = relationship("HospitalModel", back_populates="organizations")
    users = relationship("UserModel", back_populates="organization")


class RoleModel(Base):
    __tablename__ = "auth_roles"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    hospital_id = Column(String(64), ForeignKey("auth_hospitals.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(64), nullable=False)
    description = Column(String(255), nullable=True)
    created_by = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    hospital = relationship("HospitalModel", back_populates="roles")
    users = relationship("UserModel", secondary=user_roles_association, back_populates="roles")


class UserModel(Base):
    __tablename__ = "auth_users"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    hospital_id = Column(String(64), ForeignKey("auth_hospitals.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(String(64), ForeignKey("auth_organizations.id", ondelete="SET NULL"), nullable=True, index=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, index=True)
    created_by = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    hospital = relationship("HospitalModel", back_populates="users")
    organization = relationship("OrganizationModel", back_populates="users")
    roles = relationship("RoleModel", secondary=user_roles_association, back_populates="users")
    sessions = relationship("SessionModel", back_populates="user", cascade="all, delete-orphan")


class SessionModel(Base):
    __tablename__ = "auth_sessions"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(64), ForeignKey("auth_users.id", ondelete="CASCADE"), nullable=False, index=True)
    token = Column(Text, nullable=False, index=True)
    refresh_token = Column(Text, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user = relationship("UserModel", back_populates="sessions")
