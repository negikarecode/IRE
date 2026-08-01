# Insurance Reasoning Engine API Contracts Manual

This document details the **5 REST API Contracts** established between the frontend application and the backend Reasoning Engine. 

All endpoints return structured JSON contracts that Founder A can replace with real reasoning engine logic without altering frontend code.

---

## 🔌 API Endpoint Specifications

### 1. `POST /api/review-claim`
Runs full AI claim review evaluation and returns findings, denial probabilities, risk metrics, and recommendations.

**Request Payload**:
```json
{
  "claim_id": "CLM-2026-90124"
}
```

**Response Payload**:
```json
{
  "claim_id": "CLM-2026-90124",
  "status": "REVIEWED",
  "denial_probability": 0.948,
  "revenue_at_risk": 450.00,
  "ai_confidence": 0.984,
  "findings": [
    {
      "id": "FINDING-001",
      "issue": "Missing Modifier -25 on E/M Code CPT 99214",
      "why_it_matters": "Payer billing rules mandate Modifier -25 when E/M service is billed on same DOS as major surgery CPT 47562. Triggers automatic CO-50 denial.",
      "denial_probability": 0.948,
      "revenue_at_risk": 450.00,
      "supporting_evidence": "Operative note Section 3.2 documents separate E/M evaluation at 08:30 AM prior to surgery at 10:15 AM.",
      "affected_documents": ["Operative_Note_Surgical_Receipt.pdf Section 3.2"],
      "recommended_fix": "Append Modifier -25 to CPT 99214."
    }
  ],
  "recommended_fixes": [
    "Append Modifier -25 to CPT 99214.",
    "Attach Prior Auth Code BC-AUTH-99120."
  ]
}
```

---

### 2. `POST /api/run-ai`
Executes AI Scrubber rules and returns structured claims schema.

**Request Payload**:
```json
{
  "claim_id": "CLM-2026-90124"
}
```

**Response Payload**:
```json
{
  "status": "PASSED_AI_SCRUBBER",
  "confidence_score": 0.984,
  "rules_evaluated": 42,
  "rules_passed": 42,
  "structured_data": {
    "claim_id": "CLM-2026-90124",
    "patient_mrn": "MRN-90214",
    "total_billed": 12900.00,
    "payer": "BlueCross BlueShield Choice"
  }
}
```

---

### 3. `POST /api/appeal`
Generates formal reconsideration appeal letter draft and evidence checklist.

**Request Payload**:
```json
{
  "claim_id": "CLM-77019"
}
```

**Response Payload**:
```json
{
  "case_id": "APP-2026-04",
  "claim_id": "CLM-77019",
  "status": "DRAFTED",
  "denial_code": "CO-50",
  "denial_reason": "Non-covered service / Lack of medical necessity",
  "insurer": "Aetna Healthcare Choice",
  "revenue_at_risk": 1850.00,
  "appeal_letter": "To: Aetna Provider Appeals Department...\nRE: Formal Reconsideration Appeal for Claim #CLM-77019...",
  "evidence_checklist": [
    { "item": "Clinical Chart Notes", "status": "ATTACHED" },
    { "item": "Operative Report", "status": "ATTACHED" },
    { "item": "Attending Physician Signature", "status": "VERIFIED" }
  ]
}
```

---

### 4. `GET /api/claim-risk`
Calculates estimated denial probability and dollars at risk.

**Query Parameter**: `claim_id=CLM-2026-90124`

**Response Payload**:
```json
{
  "claim_id": "CLM-2026-90124",
  "revenue_at_risk": 12900.00,
  "denial_probability": 0.016,
  "risk_level": "LOW_RISK",
  "ai_confidence": 0.984
}
```

---

### 5. `GET /api/validation`
Executes pre-submission compliance validation checks.

**Query Parameter**: `claim_id=CLM-2026-90124`

**Response Payload**:
```json
{
  "claim_id": "CLM-2026-90124",
  "is_valid": true,
  "errors": [],
  "warnings": [
    {
      "code": "WARN-MOD-25",
      "message": "E/M CPT 99214 billed on same DOS as surgical CPT 47562 requires Modifier -25.",
      "severity": "MEDIUM"
    }
  ]
}
```

---

## 🌐 Live Access

Access the OpenAPI Swagger documentation live:
- Open [http://localhost:8000/docs#/Insurance%20Reasoning%20API%20Contracts](http://localhost:8000/docs#/Insurance%20Reasoning%20API%20Contracts)
