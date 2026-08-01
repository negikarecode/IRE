"""
Global Exception Handlers

Standardized exception handling for all endpoints.
No unhandled exceptions allowed.
"""

import logging
from typing import Any, Dict, Optional
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from jwt.exceptions import PyJWTError

from app.core.api_response import APIResponse
from app.core.logging_config import logger_errors

logger = logger_errors


class BaseAPIException(Exception):
    """Base exception for all API errors"""
    
    def __init__(
        self,
        message: str,
        error_code: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details
        super().__init__(message)


class UnauthorizedException(BaseAPIException):
    """Unauthorized access exception"""
    
    def __init__(self, message: str = "Unauthorized access", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "UNAUTHORIZED", status.HTTP_401_UNAUTHORIZED, details)


class ForbiddenException(BaseAPIException):
    """Forbidden access exception"""
    
    def __init__(self, message: str = "Access forbidden", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "FORBIDDEN", status.HTTP_403_FORBIDDEN, details)


class NotFoundException(BaseAPIException):
    """Resource not found exception"""
    
    def __init__(self, message: str = "Resource not found", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "NOT_FOUND", status.HTTP_404_NOT_FOUND, details)


class ConflictException(BaseAPIException):
    """Resource conflict exception"""
    
    def __init__(self, message: str = "Resource conflict", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "CONFLICT", status.HTTP_409_CONFLICT, details)


class BadRequestException(BaseAPIException):
    """Bad request exception"""
    
    def __init__(self, message: str = "Bad request", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "BAD_REQUEST", status.HTTP_400_BAD_REQUEST, details)


class ValidationException(BaseAPIException):
    """Validation exception"""
    
    def __init__(self, message: str = "Validation error", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "VALIDATION_ERROR", status.HTTP_422_UNPROCESSABLE_ENTITY, details)


class DatabaseException(BaseAPIException):
    """Database exception"""
    
    def __init__(self, message: str = "Database error", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "DATABASE_ERROR", status.HTTP_500_INTERNAL_SERVER_ERROR, details)


class ExternalServiceException(BaseAPIException):
    """External service exception"""
    
    def __init__(self, message: str = "External service error", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "EXTERNAL_SERVICE_ERROR", status.HTTP_503_SERVICE_UNAVAILABLE, details)


async def base_api_exception_handler(request: Request, exc: BaseAPIException) -> JSONResponse:
    """Handler for BaseAPIException and its subclasses"""
    logger.error(f"[API_EXCEPTION] {exc.error_code}: {exc.message} | Path: {request.url.path}")
    
    response_data, status_code = APIResponse.error(
        message=exc.message,
        error_code=exc.error_code,
        error_details=exc.details,
        status_code=exc.status_code
    )
    
    return JSONResponse(
        status_code=status_code,
        content=response_data
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handler for Pydantic validation errors"""
    logger.error(f"[VALIDATION_ERROR] {exc.errors()} | Path: {request.url.path}")
    
    # Format validation errors
    error_details = {
        "errors": [
            {
                "field": ".".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"]
            }
            for error in exc.errors()
        ]
    }
    
    response_data, status_code = APIResponse.validation_error(
        message="Request validation failed",
        error_details=error_details
    )
    
    return JSONResponse(
        status_code=status_code,
        content=response_data
    )


async def pydantic_validation_exception_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """Handler for Pydantic validation errors"""
    logger.error(f"[PYDANTIC_VALIDATION_ERROR] {exc.errors()} | Path: {request.url.path}")
    
    error_details = {
        "errors": [
            {
                "field": ".".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"]
            }
            for error in exc.errors()
        ]
    }
    
    response_data, status_code = APIResponse.validation_error(
        message="Data validation failed",
        error_details=error_details
    )
    
    return JSONResponse(
        status_code=status_code,
        content=response_data
    )


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """Handler for SQLAlchemy database errors"""
    logger.error(f"[DATABASE_ERROR] {str(exc)} | Path: {request.url.path}")
    
    response_data, status_code = APIResponse.error(
        message="Database operation failed",
        error_code="DATABASE_ERROR",
        error_details={"detail": str(exc)},
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )
    
    return JSONResponse(
        status_code=status_code,
        content=response_data
    )


async def jwt_exception_handler(request: Request, exc: PyJWTError) -> JSONResponse:
    """Handler for JWT errors"""
    logger.error(f"[JWT_ERROR] {str(exc)} | Path: {request.url.path}")
    
    response_data, status_code = APIResponse.unauthorized(
        message="Invalid or expired authentication token"
    )
    
    return JSONResponse(
        status_code=status_code,
        content=response_data
    )


from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi import HTTPException


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handler for Starlette/FastAPI HTTPExceptions"""
    logger.error(f"[HTTP_EXCEPTION] {exc.status_code}: {exc.detail} | Path: {request.url.path}")
    
    error_code_map = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        409: "CONFLICT",
        422: "VALIDATION_ERROR",
        500: "INTERNAL_ERROR"
    }
    code = error_code_map.get(exc.status_code, f"HTTP_{exc.status_code}")
    
    if isinstance(exc.detail, dict):
        msg = exc.detail.get("message") or exc.detail.get("detail") or "HTTP Exception occurred"
        code = exc.detail.get("error") or exc.detail.get("code") or code
        details = exc.detail.get("details")
        if details is None:
            details = {k: v for k, v in exc.detail.items() if k not in ["message", "error", "code", "detail", "success"]}
    else:
        msg = exc.detail if isinstance(exc.detail, str) else "HTTP Exception occurred"
        details = None

    response_data, status_code = APIResponse.error(
        message=msg,
        error_code=code,
        error_details=details,
        status_code=exc.status_code
    )
    
    return JSONResponse(
        status_code=status_code,
        content=response_data
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handler for all unhandled exceptions"""
    logger.error(f"[UNHANDLED_EXCEPTION] {type(exc).__name__}: {str(exc)} | Path: {request.url.path}", exc_info=True)
    
    response_data, status_code = APIResponse.internal_error(
        message="An unexpected error occurred",
        error_code="INTERNAL_ERROR"
    )
    
    return JSONResponse(
        status_code=status_code,
        content=response_data
    )


def register_exception_handlers(app):
    """Register all exception handlers with the FastAPI app"""
    app.add_exception_handler(BaseAPIException, base_api_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ValidationError, pydantic_validation_exception_handler)
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
    app.add_exception_handler(PyJWTError, jwt_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
