"""
Enterprise Request ID & Structured HTTP Logging Middleware
Generates unique Request IDs, tracks processing times (latency in ms),
sets context variables, and logs every API request to standard output in JSON format.
"""

import time
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, Response
from app.core.logging_config import (
    request_id_ctx,
    tenant_id_ctx,
    hospital_id_ctx,
    logger_api
)

class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that attaches a unique X-Request-ID header to every request/response,
    measures processing latency in milliseconds, and emits structured JSON logs.
    """
    async def dispatch(self, request: Request, call_next) -> Response:
        # 1. Extract or generate unique Request ID
        request_id = request.headers.get("X-Request-ID") or f"req_{uuid.uuid4().hex}"
        request_id_ctx.set(request_id)

        # 2. Extract tenant context if provided in headers
        tenant_id = request.headers.get("X-Tenant-ID") or "tenant_default"
        tenant_id_ctx.set(tenant_id)

        start_time = time.time()
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("User-Agent", "unknown")

        try:
            response = await call_next(request)
            processing_time_ms = round((time.time() - start_time) * 1000, 2)

            # Attach X-Request-ID to HTTP Response headers
            response.headers["X-Request-ID"] = request_id

            # Log HTTP request execution
            logger_api.info(
                f"HTTP {request.method} {request.url.path} -> {response.status_code} ({processing_time_ms} ms)",
                extra={
                    "event": "http_request",
                    "method": request.method,
                    "path": request.url.path,
                    "query_params": dict(request.query_params),
                    "status_code": response.status_code,
                    "processing_time_ms": processing_time_ms,
                    "client_ip": client_ip,
                    "user_agent": user_agent[:128]
                }
            )

            return response
        except Exception as exc:
            processing_time_ms = round((time.time() - start_time) * 1000, 2)
            logger_api.error(
                f"HTTP {request.method} {request.url.path} failed: {str(exc)} ({processing_time_ms} ms)",
                extra={
                    "event": "http_request_exception",
                    "method": request.method,
                    "path": request.url.path,
                    "processing_time_ms": processing_time_ms,
                    "error": str(exc),
                    "client_ip": client_ip
                },
                exc_info=True
            )
            raise exc
