import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Boolean, JSON, Integer
from app.core.database import Base

class RuleEntityModel(Base):
    """
    SQLAlchemy Database persistence model for declarative rules.
    """
    __tablename__ = "rule_definitions"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(64), nullable=False, index=True, default="default")
    rule_id = Column(String(128), nullable=False, index=True)
    group = Column(String(128), nullable=False, index=True, default="default")
    name = Column(String(255), nullable=False)
    version = Column(String(32), nullable=False, default="1.0.0")
    condition = Column(String(1024), nullable=False)
    severity = Column(String(32), nullable=False, default="WARNING")
    explanation = Column(String(1024), nullable=False)
    suggestion = Column(String(1024), nullable=False)
    priority = Column(Integer, default=100, index=True)
    actions = Column(JSON, default=list)
    dependencies = Column(JSON, default=list)
    tags = Column(JSON, default=list)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class RuleExecutionTraceModel(Base):
    """
    SQLAlchemy Database persistence model for rule execution audit logs.
    """
    __tablename__ = "rule_execution_logs"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(64), nullable=False, index=True)
    context_id = Column(String(128), nullable=False, index=True)
    group = Column(String(128), nullable=False, index=True, default="default")
    rules_fired_count = Column(Integer, default=0)
    has_critical_failures = Column(Boolean, default=False)
    report_json = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
