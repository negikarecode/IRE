# Insurance Reasoning Engine (IRE) - PostgreSQL ER Diagram

This document contains the complete Entity-Relationship (ER) diagram for the production PostgreSQL database schema, including all multi-tenant hospital relationships, primary keys, foreign keys, composite indexes, soft deletes, and audit tracking timestamps.

---

## Entity-Relationship Diagram (Mermaid)

```mermaid
erDiagram

    %% AUTHENTICATION & MULTI-TENANCY CORE
    auth_hospitals {
        string id PK
        string name
        string facility_type
        string npi_number
        datetime created_at
        datetime updated_at
    }

    auth_organizations {
        string id PK
        string hospital_id FK
        string name
        string created_by
        datetime created_at
        datetime updated_at
    }

    auth_roles {
        string id PK
        string hospital_id FK
        string name
        string description
        string created_by
        datetime created_at
        datetime updated_at
    }

    auth_users {
        string id PK
        string hospital_id FK
        string organization_id FK
        string email UK
        string hashed_password
        string full_name
        boolean is_active
        string created_by
        datetime created_at
        datetime updated_at
    }

    auth_sessions {
        string id PK
        string user_id FK
        text token
        text refresh_token
        datetime expires_at
        datetime created_at
        datetime updated_at
    }

    user_roles_association {
        string user_id PK_FK
        string role_id PK_FK
    }

    tenants {
        string id PK
        string name
        string slug UK
        string isolation_strategy
        boolean is_active
        datetime created_at
        datetime updated_at
    }

    %% PATIENT & CLAIM DOMAIN
    patients {
        string id PK
        string tenant_id FK
        string hospital_id FK
        string first_name
        string last_name
        string dob
        string medical_record_number
        boolean is_deleted
        datetime deleted_at
        string created_by
        datetime created_at
        datetime updated_at
    }

    claims {
        string id PK
        string tenant_id FK
        string patient_id FK
        string hospital_id FK
        string external_claim_ref
        string status
        float amount
        json raw_payload
        json adjudication_output
        boolean is_deleted
        datetime deleted_at
        string created_by
        datetime created_at
        datetime updated_at
    }

    %% DOCUMENT & INGESTION DOMAIN
    documents {
        string id PK
        string hospital_id FK
        string uploaded_by FK
        string claim_id FK
        string original_filename
        string internal_filename UK
        string mime_type
        integer file_size_bytes
        string storage_location
        string checksum
        string processing_status
        integer pages
        string document_type
        float classification_confidence
        integer is_manually_classified
        datetime upload_timestamp
        string virus_scan_status
        datetime virus_scan_timestamp
        string virus_scan_engine
        string retention_policy
        datetime retention_until
        integer marked_for_deletion
        datetime deleted_at
        integer access_count
        datetime last_accessed_at
        string last_accessed_by
        string created_by
        datetime created_at
        datetime updated_at
    }

    ocr_results {
        string id PK
        string document_id FK
        string hospital_id FK
        text raw_text
        json structured_data
        float ocr_confidence
        float processing_time_seconds
        integer page_count
        string detected_language
        string processing_status
        text error_message
        datetime started_at
        datetime completed_at
        string created_by
        datetime created_at
        datetime updated_at
    }

    clinical_extractions {
        string id PK
        string document_id FK
        string hospital_id FK
        string patient_name
        string uhid
        string mrn
        string age
        string gender
        string admission_date
        string discharge_date
        string operation_date
        integer length_of_stay
        string hospital
        string doctor
        string department
        text diagnosis
        json icd_codes
        text procedure
        json cpt_codes
        json medicines
        json implants
        string insurance_company
        string policy_number
        float bill_amount
        string invoice_number
        float extraction_confidence
        datetime extraction_timestamp
        string created_by
        datetime created_at
        datetime updated_at
    }

    %% BACKGROUND JOBS & ASYNC TASKING
    jobs {
        string id PK
        string hospital_id FK
        string job_type
        string status
        json payload
        json result
        text error_message
        string document_id FK
        string claim_id FK
        integer retry_count
        integer max_retries
        datetime queued_at
        datetime started_at
        datetime completed_at
        float processing_time_seconds
        string created_by
        datetime created_at
        datetime updated_at
    }

    %% REASONING & COMPLIANCE ENGINES
    validation_findings {
        string id PK
        string claim_id FK
        string hospital_id FK
        string document_id FK
        string severity
        string category
        float confidence
        string affected_document
        string affected_field
        text explanation
        text recommended_fix
        string source_document_id
        integer source_page_number
        text source_text_snippet
        string status
        string acknowledged_by
        datetime acknowledged_at
        string fixed_by
        datetime fixed_at
        datetime validation_timestamp
        string created_by
        datetime created_at
        datetime updated_at
    }

    validation_summaries {
        string id PK
        string claim_id UK_FK
        string hospital_id FK
        integer total_findings
        integer critical_findings
        integer high_findings
        integer medium_findings
        integer low_findings
        string overall_status
        float overall_confidence
        datetime validated_at
        string validated_by
        string validation_version
        string created_by
        datetime created_at
        datetime updated_at
    }

    coding_review_findings {
        string id PK
        string claim_id FK
        string hospital_id FK
        string document_id FK
        string code_type
        string code_value
        string modifier
        string severity
        string category
        float confidence
        text detected_issue
        text correct_coding_recommendation
        string reference_document
        float expected_financial_impact
        string impact_currency
        json medical_evidence
        string evidence_source_document_id
        text evidence_text_snippet
        integer evidence_page_number
        string status
        string acknowledged_by
        datetime acknowledged_at
        string fixed_by
        datetime fixed_at
        datetime review_timestamp
        string reviewed_by
        string review_version
        string created_by
        datetime created_at
        datetime updated_at
    }

    coding_review_summaries {
        string id PK
        string claim_id UK_FK
        string hospital_id FK
        integer total_findings
        integer critical_findings
        integer high_findings
        integer medium_findings
        integer low_findings
        integer icd_codes_reviewed
        integer cpt_codes_reviewed
        integer hcpcs_codes_reviewed
        float total_financial_impact
        string impact_currency
        string overall_status
        float overall_confidence
        datetime reviewed_at
        string reviewed_by
        string review_version
        string created_by
        datetime created_at
        datetime updated_at
    }

    denial_predictions {
        string id PK
        string claim_id UK_FK
        string hospital_id FK
        float denial_probability
        string risk_score
        float confidence
        float estimated_financial_exposure
        string exposure_currency
        float claim_amount
        json predicted_denial_reasons
        json contributing_factors
        float missing_documentation_score
        float authorization_score
        float coding_score
        float insurance_rules_score
        float historical_patterns_score
        float clinical_inconsistencies_score
        datetime prediction_timestamp
        string prediction_model_version
        string created_by
        datetime created_at
        datetime updated_at
    }

    revenue_leakage_findings {
        string id PK
        string claim_id FK
        string hospital_id FK
        string document_id FK
        string category
        float confidence
        float estimated_recoverable_revenue
        string revenue_currency
        text description
        text recommended_correction
        json supporting_evidence
        string affected_document
        string affected_code
        string source_document_id
        integer source_page_number
        text source_text_snippet
        string status
        string acknowledged_by
        datetime acknowledged_at
        string recovered_by
        datetime recovered_at
        float recovered_amount
        datetime detection_timestamp
        string detection_model_version
        string created_by
        datetime created_at
        datetime updated_at
    }

    revenue_leakage_summaries {
        string id PK
        string claim_id UK_FK
        string hospital_id FK
        integer total_findings
        float total_recoverable_revenue
        string revenue_currency
        integer underbilling_count
        integer missing_procedure_count
        integer missing_modifier_count
        integer missed_diagnosis_count
        integer missing_implant_count
        integer incomplete_charges_count
        integer incorrect_coding_count
        float recovered_amount
        float recovery_percentage
        datetime detection_timestamp
        string detection_model_version
        string created_by
        datetime created_at
        datetime updated_at
    }

    corrected_claim_previews {
        string id PK
        string claim_id UK_FK
        string hospital_id FK
        json original_claim_data
        json corrected_claim_data
        json ai_recommendations
        string status
        string approved_by
        datetime approved_at
        integer total_changes
        integer accepted_changes
        integer rejected_changes
        string created_by
        datetime created_at
        datetime updated_at
    }

    claim_changes {
        string id PK
        string preview_id FK
        string claim_id FK
        string hospital_id FK
        string field_name
        text original_value
        text corrected_value
        string change_type
        string source
        string source_finding_id
        string status
        string accepted_by
        datetime accepted_at
        string rejected_by
        datetime rejected_at
        string edited_by
        datetime edited_at
        text edited_value
        json ai_recommendation
        string created_by
        datetime created_at
        datetime updated_at
    }

    normalizations {
        string id PK
        string document_id FK
        string hospital_id FK
        string field_name
        string field_type
        text original_value
        text normalized_value
        string normalization_method
        float confidence
        datetime applied_at
        json context
        string created_by
        datetime created_at
        datetime updated_at
    }

    document_claims {
        string id PK
        string hospital_id FK
        string claim_number UK
        string status
        json required_document_types
        json missing_document_types
        string created_by
        datetime created_at
        datetime updated_at
    }

    %% SYSTEM AUDIT & NOTIFICATIONS
    audit_logs {
        string id PK
        string tenant_id FK
        string hospital_id FK
        string actor_id
        string action
        string resource
        string resource_id
        json details
        string created_by
        datetime created_at
        datetime updated_at
    }

    notifications {
        string id PK
        string tenant_id FK
        string hospital_id FK
        string user_id FK
        string title
        string message
        boolean is_read
        string created_by
        datetime created_at
        datetime updated_at
    }

    settings {
        string id PK
        string tenant_id FK
        string hospital_id FK
        string key
        json value
        string created_by
        datetime created_at
        datetime updated_at
    }

    %% RELATIONSHIPS & CASCADE RULES
    auth_hospitals ||--o{ auth_organizations : "owns (CASCADE)"
    auth_hospitals ||--o{ auth_roles : "owns (CASCADE)"
    auth_hospitals ||--o{ auth_users : "owns (CASCADE)"
    auth_organizations ||--o{ auth_users : "groups (SET NULL)"
    auth_users ||--o{ auth_sessions : "has (CASCADE)"
    auth_users }|--|{ auth_roles : "assigned (CASCADE)"

    patients ||--o{ claims : "submits (CASCADE)"
    claims ||--o{ documents : "attaches (SET NULL)"
    documents ||--o{ ocr_results : "generates (CASCADE)"
    documents ||--o{ clinical_extractions : "extracts (CASCADE)"

    claims ||--o{ validation_findings : "triggers (CASCADE)"
    claims ||--|| validation_summaries : "summarizes (CASCADE)"
    claims ||--o{ coding_review_findings : "reviews (CASCADE)"
    claims ||--|| coding_review_summaries : "summarizes (CASCADE)"
    claims ||--|| denial_predictions : "predicts (CASCADE)"
    claims ||--o{ revenue_leakage_findings : "detects (CASCADE)"
    claims ||--|| revenue_leakage_summaries : "summarizes (CASCADE)"

    claims ||--|| corrected_claim_previews : "previews (CASCADE)"
    corrected_claim_previews ||--o{ claim_changes : "contains (CASCADE)"
    documents ||--o{ normalizations : "normalizes (CASCADE)"
```

---

## Schema Architecture Highlights

1. **Hospital & Multi-Tenant Data Isolation**:
   - Every multi-tenant model contains an indexed `hospital_id` or `tenant_id` column.
   - Composite indexes (e.g., `(hospital_id, status)`, `(tenant_id, created_at)`) accelerate tenant-filtered queries and prevent cross-tenant data scan penalties.

2. **Cascade & Foreign Key Integrity**:
   - Deleting a hospital cascades deletions to associated organizations, users, and roles (`ondelete="CASCADE"`).
   - Deleting a user revokes all active database sessions (`ondelete="CASCADE"`).

3. **Standard Audit Fields**:
   - Every table maintains explicit `created_at` (UTC) and `updated_at` (UTC onupdate) timestamps.
   - Domain entity tables track `created_by` to maintain complete audit traceability.

4. **Soft Deletes**:
   - Tables supporting soft deletion (`patients`, `claims`, `documents`) maintain `is_deleted` and `deleted_at` attributes.
