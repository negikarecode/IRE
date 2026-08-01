"""
Production Security Middleware & Headers
"""

from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
import time
from collections import defaultdict
import logging

logger = logging.getLogger("security_middleware")

# Simple in-memory rate limiter for standard endpoint protection
class RateLimiter:
    def __init__(self, requests_per_minute: int = 120):
        self.requests_per_minute = requests_per_minute
        self.requests = defaultdict(list)

    def is_allowed(self, client_ip: str) -> bool:
        now = time.time()
        minute_ago = now - 60
        # Clean up old timestamps
        self.requests[client_ip] = [ts for ts in self.requests[client_ip] if ts > minute_ago]
        if len(self.requests[client_ip]) >= self.requests_per_minute:
            return False
        self.requests[client_ip].append(now)
        return True

rate_limiter = RateLimiter(requests_per_minute=200)


class ProductionSecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Applies HTTP Security Headers (XSS, HSTS, Framing, MIME Sniffing, CSP)
    and enforces basic IP rate limiting.
    """
    async def dispatch(self, request: Request, call_next) -> Response:
        client_ip = request.client.host if request.client else "unknown"

        # 1. Rate Limiting Check
        if not rate_limiter.is_allowed(client_ip):
            logger.warning(f"[RATE_LIMIT_EXCEEDED] Client IP: {client_ip} exceeded request limit.")
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "success": False,
                    "message": "Rate limit exceeded. Please try again later.",
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "details": {"client_ip": client_ip}
                    }
                }
            )

        response = await call_next(request)

        # 2. Production Security Headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline';"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        return response
