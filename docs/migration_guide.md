# Insurance Reasoning Engine (IRE) - Database Migration Guide

This document details the database migration procedures, Alembic setup, schema validation steps, and performance optimization guidelines for PostgreSQL deployment in production environments.

---

## 1. Overview & Architecture

The database architecture is built using **SQLAlchemy 2.0 ORM** and managed via **Alembic migrations**.

Key Database Engine Features:
- **Engine**: PostgreSQL 15+ (Production) / SQLite+aiosqlite (Local Zero-Config Dev/Test)
- **Driver**: `asyncpg` for non-blocking asynchronous I/O
- **Pool Settings**: `pool_size=20`, `max_overflow=10`, `pool_recycle=3600`, `pool_pre_ping=True`
- **Isolation Level**: Read Committed with strict tenant/hospital ID filtering

---

## 2. Alembic Configuration & Execution

Alembic configuration is housed in [`backend/alembic/env.py`](file:///home/aryan/Videos/IRE/backend/alembic/env.py).

### Generating a New Migration
To create an auto-generated migration script after updating SQLAlchemy models:

```bash
cd backend
PYTHONPATH=. alembic revision --autogenerate -m "Add index and audit fields to auth and claim models"
```

### Applying Migrations
To upgrade the database to the latest schema version:

```bash
cd backend
PYTHONPATH=. alembic upgrade head
```

### Rolling Back Migrations
To downgrade to a specific migration revision or revert the previous migration:

```bash
cd backend
PYTHONPATH=. alembic downgrade -1
```

---

## 3. Database Indexes & Query Optimization

All high-cardinality and frequently queried columns have been indexed for optimal query performance:

| Table | Index Name | Indexed Columns | Query Purpose |
| :--- | :--- | :--- | :--- |
| `auth_users` | `ix_auth_users_email` | `email` | User login lookup |
| `auth_users` | `ix_auth_users_hospital_id` | `hospital_id` | User tenant isolation |
| `patients` | `idx_patients_tenant_mrn` | `(tenant_id, medical_record_number)` | MRN search in tenant |
| `claims` | `idx_claims_hospital_status` | `(hospital_id, status)` | Filter claims by status per hospital |
| `claims` | `idx_claims_tenant_status` | `(tenant_id, status)` | Multi-tenant claim listing |
| `documents` | `idx_docs_hospital_claim` | `(hospital_id, claim_id)` | Retrieve claim documents |
| `documents` | `idx_docs_hospital_type` | `(hospital_id, document_type)` | Filter documents by type |
| `ocr_results` | `idx_ocr_doc_hosp` | `(document_id, hospital_id)` | Fast OCR lookup |
| `clinical_extractions` | `idx_clinical_doc_hosp` | `(document_id, hospital_id)` | Clinical extraction retrieval |
| `jobs` | `idx_jobs_hosp_status` | `(hospital_id, status)` | Background task status queue |
| `audit_logs` | `idx_audit_hospital_created` | `(hospital_id, created_at)` | Hospital audit trail reporting |

---

## 4. Soft Delete Policy & Data Retention

For compliance with HIPAA and healthcare record regulations:
- **Soft Deletes**: Tables `patients`, `claims`, and `documents` maintain `is_deleted: bool` and `deleted_at: timestamp`.
- **Physical Removal**: Hard deletion of binary documents and clinical data requires explicit `hard_delete=True` parameters with `HOSPITAL_ADMIN` role authorization.

---

## 5. Verification & Testing

Verify migration integrity by running the backend test suite:

```bash
cd backend
PYTHONPATH=. pytest
```
