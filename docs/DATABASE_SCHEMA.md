# Database Infrastructure & Schema Guide

The **Insurance Reasoning Engine (IRE)** enterprise database is built on **PostgreSQL 14+**.

The schema is defined in [`infrastructure/db/enterprise_schema.sql`](file:///home/aryan/Videos/IRE/infrastructure/db/enterprise_schema.sql).

## 20 Production Database Tables

| Table Name | Description | Key Indexes |
|---|---|---|
| `tenants` | Enterprise tenant accounts & status | `slug` (UNIQUE) |
| `organizations` | Multi-level organization hierarchy | `tenant_id` |
| `permissions` | System permission registry (`claims:read`) | `name` (UNIQUE) |
| `roles` | Tenant custom roles (`ADMIN`, `AUDITOR`) | `(tenant_id, name)` |
| `role_permissions` | Role-Permission mapping junction | `(role_id, permission_id)` |
| `users` | User credentials & tenant assignments | `(tenant_id, email)` |
| `user_roles` | User-Role mapping junction | `(user_id, role_id)` |
| `hospitals` | Hospitals, facilities, and NPI numbers | `tenant_id`, `npi_number` |
| `patients` | Master Patient Index (MPI) demographics | `(tenant_id, mrn)` |
| `admissions` | Hospital admissions & clinical summaries | `patient_id`, `tenant_id` |
| `claims` | Claims lifecycle state machine & JSONB payloads | `(tenant_id, status)`, `external_claim_ref` |
| `files` | Binary file metadata, S3 paths, SHA-256 hashes | `tenant_id` |
| `documents` | Extracted document classifications (EOB, UB-04) | `claim_id`, `tenant_id` |
| `ocr_results` | Extracted text, bounding boxes, OCR confidence | `document_id` |
| `ai_results` | Autonomous AI reasoning chains & HITL flags | `claim_id` |
| `events` | Transactional Outbox pattern event queue | `(status, created_at)` |
| `notifications` | In-app, Email, SMS, Webhook notifications | `(tenant_id, user_id, is_read)` |
| `audit_logs` | SHA-256 cryptographic hash-chained audit trail | `(tenant_id, resource, resource_id)` |
| `activity_logs` | HTTP access telemetry, duration, client IP | `(tenant_id, user_id, created_at)` |
| `version_history` | Entity revision snapshot history and JSON diffs | `(tenant_id, entity_name, entity_id, version_number)` |

## Multi-Tenant Row-Level Security (RLS)

All tenant-scoped tables enforce PostgreSQL Row-Level Security:

```sql
ALTER TABLE claims ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_claims ON claims 
    FOR ALL 
    USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);
```
