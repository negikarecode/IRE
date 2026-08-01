from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.v1.router import api_router
from app.api.endpoints.reasoning import router as reasoning_router
from app.core.database import init_db

from app.core.exceptions import register_exception_handlers
from app.core.api_response import APIResponse

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB tables on startup
    await init_db()
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Insurance Reasoning Engine (IRE) - Clean Architecture FastAPI Backend Skeleton",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan
)

from app.core.logging_config import setup_enterprise_logging
from app.core.logging_middleware import StructuredLoggingMiddleware
from app.core.security_middleware import ProductionSecurityHeadersMiddleware

# Setup Enterprise JSON Logging
setup_enterprise_logging(level="INFO")

# Register global exception handlers (No unhandled exceptions allowed)
register_exception_handlers(app)

# Register Enterprise Logging Middleware (Request ID & Latency Tracking)
app.add_middleware(StructuredLoggingMiddleware)

# Register Security Headers & Rate Limiting Middleware
app.add_middleware(ProductionSecurityHeadersMiddleware)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Gateway v1 router
app.include_router(api_router, prefix=settings.API_V1_STR)
# Include top-level reasoning API contracts under /api
app.include_router(reasoning_router, prefix="/api", tags=["Insurance Reasoning API Contracts"])

@app.get("/")
async def root():
    return {
        "success": True,
        "message": "Insurance Reasoning Engine API is operational",
        "data": {
            "title": settings.PROJECT_NAME,
            "version": "1.0.0",
            "docs": f"{settings.API_V1_STR}/docs",
            "status": "OPERATIONAL"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
