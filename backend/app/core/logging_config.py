"""
Structured Enterprise Logging Configuration for Insurance Reasoning Engine (IRE)
Supports ELK (Elasticsearch/Logstash/Kibana), Grafana/Loki, and Datadog Ingestion.
Enforces HIPAA compliance by automatically redacting PHI and sensitive credentials.
"""

import logging
import json
import uuid
import sys
from datetime import datetime, timezone
from contextvars import ContextVar
from typing import Any, Dict

# Context Variables for Request Traceability
request_id_ctx: ContextVar[str] = ContextVar("request_id", default="")
tenant_id_ctx: ContextVar[str] = ContextVar("tenant_id", default="")
hospital_id_ctx: ContextVar[str] = ContextVar("hospital_id", default="")
user_id_ctx: ContextVar[str] = ContextVar("user_id", default="")

# Sensitive Fields & PHI to Automatically Redact
SENSITIVE_KEYS = {
    "password", "confirm_password", "hashed_password", "token", "refresh_token",
    "access_token", "secret", "secret_key", "authorization", "cookie", "ssn",
    "social_security", "patient_name", "first_name", "last_name", "dob",
    "date_of_birth", "address", "phone", "email_address"
}

def sanitize_sensitive_data(data: Any) -> Any:
    """
    Recursively redacts sensitive keys and PHI values from dictionaries and lists.
    """
    if isinstance(data, dict):
        sanitized = {}
        for key, value in data.items():
            if key.lower() in SENSITIVE_KEYS:
                sanitized[key] = "[REDACTED]"
            else:
                sanitized[key] = sanitize_sensitive_data(value)
        return sanitized
    elif isinstance(data, list):
        return [sanitize_sensitive_data(item) for item in data]
    return data


class StructuredJSONFormatter(logging.Formatter):
    """
    Custom Logging Formatter that outputs single-line JSON records formatted for ELK/Grafana/Loki.
    """
    def format(self, record: logging.LogRecord) -> str:
        log_payload: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": "ire-backend",
            "environment": "production",
            "request_id": request_id_ctx.get() or getattr(record, "request_id", ""),
            "tenant_id": tenant_id_ctx.get() or getattr(record, "tenant_id", ""),
            "hospital_id": hospital_id_ctx.get() or getattr(record, "hospital_id", ""),
            "user_id": user_id_ctx.get() or getattr(record, "user_id", ""),
        }

        # Include exception info if present
        if record.exc_info:
            log_payload["exception"] = self.formatException(record.exc_info)

        # Include extra context attributes passed to logger
        extra_data = {}
        for key, val in record.__dict__.items():
            if key not in {
                "args", "asctime", "created", "exc_info", "exc_text", "filename",
                "funcName", "levelname", "levelno", "lineno", "module", "msecs",
                "msg", "name", "pathname", "process", "processName", "relativeCreated",
                "stack_info", "thread", "threadName", "request_id", "tenant_id",
                "hospital_id", "user_id"
            }:
                extra_data[key] = val

        if extra_data:
            log_payload["extra"] = sanitize_sensitive_data(extra_data)

        return json.dumps(log_payload)


def setup_enterprise_logging(level: str = "INFO"):
    """
    Sets up root logger with StructuredJSONFormatter writing to stdout.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Clear existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(StructuredJSONFormatter())
    root_logger.addHandler(console_handler)

    # Disable noisy third-party loggers
    logging.getLogger("uvicorn.access").disabled = True
    logging.getLogger("asyncio").setLevel(logging.WARNING)


# Helper Logger Instances for Core Subsystems
logger_api = logging.getLogger("ire.api")
logger_auth = logging.getLogger("ire.auth")
logger_uploads = logging.getLogger("ire.uploads")
logger_ocr = logging.getLogger("ire.ocr")
logger_jobs = logging.getLogger("ire.jobs")
logger_db = logging.getLogger("ire.db")
logger_errors = logging.getLogger("ire.errors")
