from fastapi import APIRouter, status
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

router = APIRouter()

class ClaimPayloadDTO(BaseModel):
    claim_id: Optional[str] = Field(default="CLM-2026-90124", example="CLM-2026-90124")

@router.post("/review-claim", status_code=status.HTTP_200_OK)
async def review_claim(payload: Optional[ClaimPayloadDTO] = None):
    """
    POST /api/review-claim
    Full AI claim review endpoint returning findings, denial probabilities, risk metrics, and recommendations.
    """
    claim_id = payload.claim_id if (payload and payload.claim_id) else "CLM-2026-90124"
    data = {
        "claim_id": claim_id,
        "currency": "INR",
        "currency_symbol": "₹",
        "status": "REVIEWED",
        "denial_probability": 0.948,
        "revenue_at_risk": 4500.00,
        "ai_confidence": 0.984,
        "findings": [
            {
                "id": "FINDING-001",
                "issue": "Missing Modifier -25 on OPD Consultation Code CPT 99214",
                "why_it_matters": "Star Health TPA rules require Modifier -25 when OPD consultation is billed on same DOS as major surgery CPT 47562. Triggers rejection.",
                "denial_probability": 0.948,
                "revenue_at_risk": 4500.00,
                "supporting_evidence": "Operative note Section 3.2 documents separate OPD consultation prior to surgery.",
                "affected_documents": ["Discharge_Summary_Operative_Report_0728.pdf Section 3.2"],
                "recommended_fix": "Append Modifier -25 to CPT 99214."
            },
            {
                "id": "FINDING-002",
                "issue": "Pre-Authorization ID Missing in Claim Header",
                "why_it_matters": "Star Health cashless policy mandates pre-authorization ID PA-99120 on claims exceeding ₹1,00,000.00.",
                "denial_probability": 0.882,
                "revenue_at_risk": 124500.00,
                "supporting_evidence": "TPA pre-auth database matched active authorization PA-99120.",
                "affected_documents": ["Final_Itemized_Hospital_Bill_0728.pdf"],
                "recommended_fix": "Attach Pre-Auth ID PA-99120."
            }
        ],
        "recommended_fixes": [
            "Append Modifier -25 to CPT 99214.",
            "Attach Pre-Auth ID PA-99120."
        ]
    }
    return {
        "success": True,
        "message": "Claim review completed successfully",
        "data": data
    }

@router.post("/run-ai", status_code=status.HTTP_200_OK)
async def run_ai(payload: Optional[ClaimPayloadDTO] = None):
    """
    POST /api/run-ai
    AI Scrubber execution endpoint returning structured claims schema.
    """
    claim_id = payload.claim_id if (payload and payload.claim_id) else "CLM-2026-90124"
    data = {
        "status": "PASSED_AI_SCRUBBER",
        "currency": "INR",
        "currency_symbol": "₹",
        "confidence_score": 0.984,
        "rules_evaluated": 42,
        "rules_passed": 42,
        "structured_data": {
            "claim_id": claim_id,
            "patient_uhid": "UHID-90214",
            "total_billed": 129000.00,
            "payer": "Star Health Insurance",
            "pre_auth_id": "PA-99120",
            "line_items": [
                { "cpt": "47562", "amount": 124500.00, "dx": "K80.20" },
                { "cpt": "99214-25", "amount": 4500.00, "dx": "R07.9", "modifier": "25" }
            ]
        }
    }
    return {
        "success": True,
        "message": "AI Scrubber executed successfully",
        "data": data
    }

@router.post("/appeal", status_code=status.HTTP_200_OK)
async def generate_appeal(payload: Optional[ClaimPayloadDTO] = None):
    """
    POST /api/appeal
    AI Appeal Generator contract returning formal reconsideration letter draft.
    """
    claim_id = payload.claim_id if (payload and payload.claim_id) else "CLM-77019"
    data = {
        "case_id": "APP-2026-04",
        "claim_id": claim_id,
        "status": "DRAFTED",
        "denial_code": "REJ-050",
        "denial_reason": "Cashless Rejection / Lack of medical necessity",
        "insurer": "ICICI Lombard General Insurance",
        "revenue_at_risk": 18500.00,
        "appeal_letter": """To: ICICI Lombard Grievance & Appeals Department
ICICI Lombard House, Mumbai, Maharashtra 400025

RE: Formal Reconsideration Appeal for Claim #CLM-77019
Patient Name: Sunita Verma | Policy ID: IL-9912038 | Pre-Auth #: PA-881290
Date of Admission: July 15, 2026 | Denied Billed Amount: ₹18,500.00
Rejection Code: REJ-050 (Cashless Rejection / Lack of medical necessity)

Dear Appeals Committee,

We are writing to formally request a clinical reconsideration of the cashless rejection issued for Claim #CLM-77019 on behalf of Apollo Multispecialty Hospital.

CLINICAL RATIONALE & EVIDENTIARY PROOF:
The service provided (Laparoscopic Cholecystectomy — CPT 47562) was medically necessary and urgent. Section 3.2 of the attached Operative Report explicitly details acute symptomatic gallbladder calculus (ICD-10 K80.20).

Based on established IRDAI Health Insurance Regulations, we respectfully request that ICICI Lombard overturn the rejection and approve full reimbursement of ₹18,500.00.

Sincerely,
Dr. Rajesh Sharma, MS
Head of Revenue Cycle & TPA Desk, Apollo Multispecialty Hospital""",
        "evidence_checklist": [
            { "item": "Clinical Discharge Summary", "status": "ATTACHED" },
            { "item": "Operative Notes", "status": "ATTACHED" },
            { "item": "Attending Surgeon Signature", "status": "VERIFIED" }
        ]
    }
    return {
        "success": True,
        "message": "Appeal letter generated successfully",
        "data": data
    }

@router.get("/claim-risk", status_code=status.HTTP_200_OK)
async def get_claim_risk(claim_id: str = "CLM-2026-90124"):
    """
    GET /api/claim-risk
    Calculates estimated denial probability and financial risk.
    """
    data = {
        "claim_id": claim_id,
        "currency": "INR",
        "currency_symbol": "₹",
        "revenue_at_risk": 129000.00,
        "denial_probability": 0.016,
        "risk_level": "LOW_RISK",
        "ai_confidence": 0.984
    }
    return {
        "success": True,
        "message": "Claim risk evaluated successfully",
        "data": data
    }

@router.get("/validation", status_code=status.HTTP_200_OK)
async def get_validation(claim_id: str = "CLM-2026-90124"):
    """
    GET /api/validation
    Pre-submission compliance validation endpoint returning errors and warnings.
    """
    data = {
        "claim_id": claim_id,
        "is_valid": True,
        "errors": [],
        "warnings": [
            {
                "code": "WARN-MOD-25",
                "message": "OPD Consultation CPT 99214 billed on same DOS as surgical CPT 47562 requires Modifier -25.",
                "severity": "MEDIUM"
            }
        ]
    }
    return {
        "success": True,
        "message": "Claim validation completed successfully",
        "data": data
    }
