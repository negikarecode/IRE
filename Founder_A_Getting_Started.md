# Founder A Getting Started Guide: Extending the Insurance Reasoning Engine (IRE) Platform

Welcome to the **Insurance Reasoning Engine (IRE)** platform. This guide serves as the authoritative blueprint for **Founder A** and domain engineers to extend business logic, medical rules, risk scoring models, AI validators, recommendation engines, and appeal generators **without modifying core platform infrastructure**.

---

## 🛑 The Golden Rule of Architecture

> [!CAUTION]
> **Founder A Should Never Modify Infrastructure**:  
> Core files in `app/core/`, `app/infrastructure/`, database connections (`database.py`), HTTP middleware (`security_middleware.py`, `logging_middleware.py`), and global exception handlers (`exceptions.py`) are core infrastructure assets.  
> **All custom rules, engines, and domain logic MUST be implemented as standalone plugins using the Business Logic SDK (`app/sdk/`).**

---

## 1. Platform Architecture Overview

The Insurance Reasoning Engine is architected around a decoupled **Clean Architecture + SDK Plugin System**:

```
+-----------------------------------------------------------------------+
|                         API Gateway (/api/v1)                         |
+-----------------------------------------------------------------------+
|   Auth (/auth)  |  Documents (/documents)  |  Claims (/v1_core/claims) |
+-----------------------------------------------------------------------+
                                   |
                                   v
+-----------------------------------------------------------------------+
|                     Business Logic SDK (app/sdk/)                     |
|           Plugin Registry & Automatic Extension Point Discovery       |
+-----------------------------------------------------------------------+
       |               |                 |                 |
       v               v                 v                 v
+--------------+ +--------------+ +---------------+ +------------------+
| Custom Rules | | Custom       | | Custom Risk   | | Custom Appeal    |
| Plugins      | | Validators   | | Engines       | | Engines          |
+--------------+ +--------------+ +---------------+ +------------------+
                                   |
                                   v
+-----------------------------------------------------------------------+
|                    Core Infrastructure & Storage                      |
| PostgreSQL (SQLAlchemy) | Local/S3 Object Storage | Async OCR Queue   |
+-----------------------------------------------------------------------+
```

---

## 2. Codebase Folder Structure

```
backend/
├── alembic/                      # Database migrations
├── app/
│   ├── api/                      # REST API endpoints & Gateway routing
│   │   ├── endpoints/            # Auth, Claims, Documents, OCR, Reasoning
│   │   └── v1/router.py          # Central API v1 router
│   ├── core/                     # CORE INFRASTRUCTURE (DO NOT MODIFY)
│   │   ├── api_response.py       # Standard Success/Error JSON contracts
│   │   ├── database.py           # Async SQLAlchemy database engine
│   │   ├── dependencies.py       # JWT auth & RBAC dependencies
│   │   ├── exceptions.py         # Global exception handlers
│   │   ├── logging_config.py     # Enterprise JSON log formatter
│   │   ├── logging_middleware.py # Request ID tracing & latency middleware
│   │   ├── security.py           # Bcrypt & JWT security utilities
│   │   └── security_middleware.py# CORS, Rate Limiting & Security Headers
│   ├── infrastructure/           # INFRASTRUCTURE ADAPTERS (DO NOT MODIFY)
│   │   ├── db/models/            # PostgreSQL ORM models
│   │   ├── storage/              # S3 / Local Object Storage adapter
│   │   └── services/             # Virus scan & OCR services
│   ├── ocr/                      # OCR pipeline, queue & converters
│   └── sdk/                      # FOUNDER A EXTENSION SDK (USE THIS)
│       ├── base.py               # Abstract Base Plugin & Metadata schemas
│       ├── decorators.py         # @register_rule, @register_validator, etc.
│       ├── discovery.py          # Auto-plugin discovery engine
│       ├── extension_points.py   # Abstract Extension Point classes
│       └── registry.py           # In-memory Plugin Registry
├── docs/                         # OpenAPI specs, ER diagrams, Migration guides
├── scripts/                      # Utility scripts
└── tests/                        # Test suite (50 passing tests)
```

---

## 3. End-to-End System Flows

### 3.1 Document Flow
1. **Upload Request**: Client sends document via `POST /api/v1/documents/upload`.
2. **Streaming Buffer**: File is read via **64 KB streaming buffers** to ensure minimal RAM usage (< 1 MB footprint per request).
3. **Validation & Scanning**: MIME type, extension whitelist (`.pdf`, `.jpg`, `.png`, `.tiff`), and SHA-256 checksum are verified. File passes through virus scan check.
4. **Storage & Metadata**: File bytes are saved to Object Storage (`/tmp/ire_uploads` or AWS S3). Metadata is saved to PostgreSQL `documents` table with tenant/hospital isolation.

### 3.2 OCR Flow
1. **Enqueue Task**: Document upload triggers `async_ocr_queue.enqueue_ocr_job(...)`.
2. **Format Conversion**: PDF pages are rendered to high-DPI images via `format_converter`.
3. **Layout & Text Extraction**: OCR Engine extracts raw text, bounding boxes, tables, and detected language.
4. **Persistence**: Structured output is saved to PostgreSQL `ocr_results` table.

### 3.3 Claim Flow & AI Reasoning Pipeline
```
[Ingested Claim] ──> [Patient MRN Link] ──> [Document Attachment]
                                                    │
    ┌───────────────────────────────────────────────┴──────────────────────────────────────────────┐
    │                                                                                              │
    v                                               v                                              v
[1. AI Validation]                           [2. Medical Coding Review]                 [3. Denial Risk Engine]
Validates pre-auth,                          Detects ICD/CPT mismatches,                 Calculates denial risk (0.0-1.0)
signatures, required docs                    unbundling, missing modifiers               & contributing factors
    │                                               │                                              │
    └───────────────────────────────────────────────┼──────────────────────────────────────────────┘
                                                    │
                                                    v
                                    [4. Revenue Leakage Detection]
                                    Identifies missed implants & unbilled charges
                                                    │
                                                    v
                                    [5. Corrected Claim Preview]
                                    Generates diffs & AI recommendations for reviewer
                                                    │
                                                    v
                                    [6. Automated Appeal Generator]
                                    Generates formal appeal letter package
```

---

## 4. PostgreSQL Database Schema & Isolation

All database tables follow strict multi-tenant isolation rules:
- **Tenant Isolation**: Every entity contains indexed `hospital_id` or `tenant_id` fields.
- **Audit Columns**: Every table maintains `created_at` (UTC), `updated_at` (UTC onupdate), and `created_by`.
- **Soft Deletes**: Key domain entities (`patients`, `claims`, `documents`) maintain `is_deleted` and `deleted_at`.
- **Performance Indexes**: B-tree composite indexes (`hospital_id, status`, `tenant_id, created_at`) ensure `< 5 ms` query performance.

---

## 5. API Gateway & Security Standards

- **Endpoint Prefix**: All endpoints are mounted under `/api/v1`.
- **Authentication**: `Authorization: Bearer <JWT>` header required for all non-public endpoints.
- **Request Tracing**: `X-Request-ID` is assigned to every request and returned in response headers.
- **Standard Envelope**:
  - Success: `{"success": true, "message": "...", "data": {...}}`
  - Error: `{"success": false, "message": "...", "error": {"code": "...", "details": {...}}}`

---

## 6. Business Logic SDK Extension Points

Founder A can extend the platform across 9 extension points using standard Python decorators from `app.sdk.decorators`:

| Extension Point | Decorator | Base Class | Purpose |
| :--- | :--- | :--- | :--- |
| **1. Rules** | `@register_rule` | `BaseRulePlugin` | Custom rule evaluation (e.g. policy limits, age restrictions) |
| **2. Validators** | `@register_validator` | `BaseValidatorPlugin` | Custom payload & document validation |
| **3. Risk Engines** | `@register_risk_engine` | `BaseRiskEnginePlugin` | Risk scoring & denial probability algorithms |
| **4. Policy Providers** | `@register_policy_provider` | `BasePolicyProviderPlugin` | Enterprise policy & contract lookup |
| **5. Medical Extractors** | `@register_medical_extractor` | `BaseMedicalExtractorPlugin` | Clinical entity, ICD, and CPT extraction |
| **6. Reasoning Pipelines**| `@register_reasoning_pipeline`| `BaseReasoningPipelinePlugin`| Multi-stage recommendation & reasoning logic |
| **7. AI Agents** | `@register_agent` | `BaseAgentPlugin` | Autonomous goal-oriented agents |
| **8. Appeal Engines** | `@register_appeal_engine` | `BaseAppealEnginePlugin` | Automated denial appeal package generation |
| **9. Package Validators**| `@register_package_validator` | `BasePackageValidatorPlugin` | Release package manifest validation |

---

## 7. Concrete Code Examples for Founder A

Create custom plugin files anywhere under `backend/app/plugins/` (or any custom plugin folder). The platform will automatically discover and register them upon startup!

### Example 1: Building a Custom Rule (`@register_rule`)
Create `app/plugins/custom_policy_rule.py`:

```python
from typing import Dict, Any
from app.sdk.base import BaseRulePlugin
from app.sdk.decorators import register_rule

@register_rule(
    plugin_id="rule_high_value_claim",
    name="High Value Claim Threshold Rule",
    version="1.0.0",
    description="Flags claims exceeding $10,000 for secondary medical review"
)
class HighValueClaimRule(BaseRulePlugin):
    async def evaluate_rule(self, context: Dict[str, Any]) -> Dict[str, Any]:
        claim_amount = context.get("amount", 0.0)
        threshold = 10000.0
        
        requires_secondary_review = claim_amount > threshold
        return {
            "rule_id": self.metadata.plugin_id,
            "passed": not requires_secondary_review,
            "claim_amount": claim_amount,
            "requires_secondary_review": requires_secondary_review,
            "reason": f"Claim amount ${claim_amount:,.2f} exceeds secondary review threshold of ${threshold:,.2f}" if requires_secondary_review else "Within threshold"
        }
```

---

### Example 2: Building a Custom Validator (`@register_validator`)
Create `app/plugins/custom_document_validator.py`:

```python
from typing import Dict, Any
from app.sdk.base import BaseValidatorPlugin
from app.sdk.decorators import register_validator

@register_validator(
    plugin_id="val_discharge_summary_complete",
    name="Discharge Summary Completeness Validator",
    version="1.0.0",
    description="Validates presence of essential clinical sections in discharge summary"
)
class DischargeSummaryValidator(BaseValidatorPlugin):
    async def validate_payload(self, data: Dict[str, Any]) -> Dict[str, Any]:
        extracted_text = data.get("text", "").lower()
        required_sections = ["history", "diagnosis", "treatment", "discharge condition"]
        
        missing_sections = [sec for sec in required_sections if sec not in extracted_text]
        is_valid = len(missing_sections) == 0
        
        return {
            "validator_id": self.metadata.plugin_id,
            "is_valid": is_valid,
            "missing_sections": missing_sections,
            "score": (len(required_sections) - len(missing_sections)) / len(required_sections)
        }
```

---

### Example 3: Building a Custom Risk Engine (`@register_risk_engine`)
Create `app/plugins/custom_risk_engine.py`:

```python
from typing import Dict, Any
from app.sdk.base import BaseRiskEnginePlugin
from app.sdk.decorators import register_risk_engine

@register_risk_engine(
    plugin_id="risk_readmission_probability",
    name="Hospital Readmission Risk Engine",
    version="1.0.0",
    description="Calculates 30-day hospital readmission risk score based on clinical factors"
)
class ReadmissionRiskEngine(BaseRiskEnginePlugin):
    async def calculate_risk(self, entity_data: Dict[str, Any]) -> Dict[str, Any]:
        length_of_stay = entity_data.get("length_of_stay", 1)
        age = entity_data.get("age", 40)
        icd_codes = entity_data.get("icd_codes", [])
        
        # Risk scoring logic
        base_risk = 0.1
        if length_of_stay > 7:
            base_risk += 0.25
        if age > 65:
            base_risk += 0.20
        if len(icd_codes) > 3:
            base_risk += 0.15
            
        risk_score = min(base_risk, 1.0)
        risk_category = "HIGH" if risk_score > 0.6 else "MEDIUM" if risk_score > 0.3 else "LOW"
        
        return {
            "engine_id": self.metadata.plugin_id,
            "risk_score": round(risk_score, 2),
            "risk_category": risk_category,
            "contributing_factors": {
                "length_of_stay": length_of_stay,
                "patient_age": age,
                "comorbidities_count": len(icd_codes)
            }
        }
```

---

### Example 4: Building a Recommendation Engine (`@register_reasoning_pipeline`)
Create `app/plugins/custom_recommendation_engine.py`:

```python
from typing import Dict, Any
from app.sdk.base import BaseReasoningPipelinePlugin
from app.sdk.decorators import register_reasoning_pipeline

@register_reasoning_pipeline(
    plugin_id="reasoning_claim_optimization",
    name="Claim Optimization & Recommendation Engine",
    version="1.0.0",
    description="Generates actionable claim coding recommendations prior to payer submission"
)
class ClaimOptimizationRecommendationEngine(BaseReasoningPipelinePlugin):
    async def run_pipeline(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        cpt_codes = input_data.get("cpt_codes", [])
        diagnosis = input_data.get("diagnosis", "")
        
        recommendations = []
        if "99214" in cpt_codes and "hypertension" in diagnosis.lower():
            recommendations.append({
                "type": "MODIFIER_RECOMMENDATION",
                "recommended_modifier": "25",
                "reason": "Significant, separately identifiable evaluation and management service on same day",
                "financial_impact_estimate": 45.00
            })
            
        return {
            "pipeline_id": self.metadata.plugin_id,
            "total_recommendations": len(recommendations),
            "recommendations": recommendations
        }
```

---

### Example 5: Building an Appeal Generator (`@register_appeal_engine`)
Create `app/plugins/custom_appeal_generator.py`:

```python
from typing import Dict, Any
from app.sdk.base import BaseAppealEnginePlugin
from app.sdk.decorators import register_appeal_engine

@register_appeal_engine(
    plugin_id="appeal_medical_necessity_generator",
    name="Medical Necessity Appeal Letter Generator",
    version="1.0.0",
    description="Automates generation of formal denial appeal letters backed by clinical evidence"
)
class MedicalNecessityAppealGenerator(BaseAppealEnginePlugin):
    async def process_appeal(self, appeal_case: Dict[str, Any]) -> Dict[str, Any]:
        claim_ref = appeal_case.get("claim_ref", "CLM-UNKNOWN")
        patient_name = appeal_case.get("patient_name", "Patient")
        denial_reason = appeal_case.get("denial_reason", "Lack of Medical Necessity")
        clinical_evidence = appeal_case.get("clinical_evidence", "Discharge summary confirms acute condition requiring inpatient admission.")
        
        appeal_letter = f"""
FORMAL CLAIM DENIAL APPEAL
--------------------------------------------------
Claim Reference: {claim_ref}
Patient: {patient_name}
Re: Appeal against denial based on '{denial_reason}'

Dear Appeals Committee,

We are writing to formally appeal the denial of claim {claim_ref}.
The medical documentation clearly establishes medical necessity for the rendered services.

CLINICAL EVIDENCE:
{clinical_evidence}

We respectfully request immediate reconsideration and full reimbursement of this claim.

Sincerely,
Billing & Appeals Department
        """.strip()
        
        return {
            "appeal_engine_id": self.metadata.plugin_id,
            "claim_ref": claim_ref,
            "appeal_status": "GENERATED",
            "appeal_letter_text": appeal_letter
        }
```

---

## 8. Verifying Your Plugins

Run the plugin registry discovery test to confirm all custom plugins are registered:

```bash
cd backend
PYTHONPATH=. pytest tests/test_business_logic_sdk.py -v
```

All custom plugins will automatically register and become available via the SDK Plugin Registry (`plugin_registry.get(...)`) and API endpoints without modifying a single line of core infrastructure!
