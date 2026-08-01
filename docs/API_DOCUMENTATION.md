# API Documentation & Schema Contracts

The **Insurance Reasoning Engine (IRE)** provides an **API-First** specification across REST and gRPC protocols.

## Interactive API Specifications

- **Swagger UI**: Available at `http://localhost:8000/api/v1/docs` when running the backend.
- **ReDoc Specification**: Available at `http://localhost:8000/api/v1/redoc`.
- **OpenAPI 3.0 YAML File**: [`api/openapi/ire_openapi_v1.yaml`](file:///home/aryan/Videos/IRE/api/openapi/ire_openapi_v1.yaml)
- **gRPC Protobuf File**: [`api/proto/ire_services.proto`](file:///home/aryan/Videos/IRE/api/proto/ire_services.proto)

## Core API Endpoint Groups

| Endpoint Group | Base Path | Description |
|---|---|---|
| **Health Checks** | `/api/v1/healthz`, `/api/v1/readyz` | Liveness and database connectivity readiness probes. |
| **Authentication** | `/api/v1/auth/login`, `/api/v1/auth/register` | JWT token issuance and user registration. |
| **Tenant Management** | `/api/v1/tenants/` | Multi-tenant account provisioning and isolation settings. |
| **Role Management & RBAC** | `/api/v1/roles/` | Custom role creation and permission assignments. |
| **Hospital Management** | `/api/v1/hospitals/` | Hospital facility registry and NPI number indexing. |
| **Patient Management** | `/api/v1/patients/` | Master Patient Index (MPI) demographics. |
| **Claim Management** | `/api/v1/claims/` | Ingest claims and trigger `IClaimProcessor` interface execution. |
| **Document Uploads** | `/api/v1/documents/upload` | Multipart file upload and Celery background task processing. |
| **AI Gateway** | `/api/v1/ai/generate`, `/api/v1/ai/models` | Multi-provider LLM text generation and model capabilities. |
| **Modular OCR** | `/api/v1/ocr/extract` | Document layout, text, handwriting, and table extraction into JSON. |
| **Rule Engine** | `/api/v1/rules/execute`, `/api/v1/rules/register` | Auto-execute declarative rules, test conditions, and install plugins. |
| **Agent Framework** | `/api/v1/agents/run`, `/api/v1/agents/register` | Execute autonomous agent ReAct workflows and view metrics. |
| **Integration Platform** | `/api/v1/integration/send`, `/api/v1/integration/dlq` | Send REST/SOAP/FHIR/HL7 messages and manage Dead Letter Queue. |
