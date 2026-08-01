from fastapi import APIRouter
from app.api.v1.endpoints import (
    health, auth, tenants, roles, hospitals,
    patients, claims, documents, notifications,
    audit, settings, ai_gateway, ocr, rules, agent_framework,
    integration, users, organizations, patient_claim, document_management, sdk, document_claims, jobs, sse, validation, coding_review, denial_prediction, revenue_leakage, corrected_claim
)

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health Checks"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication & JWT"])
api_router.include_router(users.router, prefix="/users", tags=["User Management & Profile"])
api_router.include_router(organizations.router, prefix="/organizations", tags=["Organization Management"])
api_router.include_router(tenants.router, prefix="/tenants", tags=["Tenant Management"])
api_router.include_router(roles.router, prefix="/roles", tags=["Role Management & RBAC"])
api_router.include_router(hospitals.router, prefix="/hospitals", tags=["Hospital Management"])
api_router.include_router(patients.router, prefix="/patients", tags=["Patient Management"])
api_router.include_router(claims.router, prefix="/claims", tags=["Claim Management"])
api_router.include_router(patient_claim.router, prefix="/v1_core", tags=["Patient & Claim Management API"])
api_router.include_router(document_management.router, prefix="/v1_docs", tags=["Enterprise Document Management Platform"])
api_router.include_router(documents.router, prefix="/documents", tags=["Document Management & Uploads"])
api_router.include_router(document_claims.router, prefix="/document-claims", tags=["Document Claim Assembly"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["Job Queue & Background Processing"])
api_router.include_router(sse.router, prefix="/sse", tags=["Server-Sent Events (Real-time Updates)"])
api_router.include_router(validation.router, prefix="/validation", tags=["AI Claim Validation"])
api_router.include_router(coding_review.router, prefix="/coding-review", tags=["AI Medical Coding Review"])
api_router.include_router(denial_prediction.router, prefix="/denial-prediction", tags=["AI Denial Prediction"])
api_router.include_router(revenue_leakage.router, prefix="/revenue-leakage", tags=["Revenue Leakage Detection"])
api_router.include_router(corrected_claim.router, prefix="/corrected-claim", tags=["Corrected Claim Preview"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["Notification System"])
api_router.include_router(audit.router, prefix="/audit", tags=["Audit Logs"])
api_router.include_router(settings.router, prefix="/settings", tags=["Settings"])
api_router.include_router(ai_gateway.router, prefix="/ai", tags=["AI Infrastructure Gateway"])
api_router.include_router(ocr.router, prefix="/ocr", tags=["Modular OCR Service"])
api_router.include_router(rules.router, prefix="/rules", tags=["Generic Rule Engine Framework"])
api_router.include_router(agent_framework.router, prefix="/agents", tags=["Autonomous Agent Framework"])
api_router.include_router(integration.router, prefix="/integration", tags=["Enterprise Integration Platform"])
api_router.include_router(sdk.router, prefix="/sdk", tags=["Founder A Business Logic SDK"])
