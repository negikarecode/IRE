# Complete Directory Structure & Folder Rationale

Below is the complete file and folder structure of the **Insurance Reasoning Engine (IRE)** workspace with explanations for why every folder exists.

```
/home/aryan/Videos/IRE
├── package.json                          # Monorepo root dependencies & scripts
├── pnpm-workspace.yaml                   # Monorepo workspace boundaries
├── tsconfig.base.json                    # Global strict TypeScript configuration
├── docker-compose.yml                    # Local multi-container development setup
├── docker-compose.prod.yml               # Production multi-container setup with Nginx SSL
├── README.md                             # Master repository entrypoint & sitemap
│
├── .github/                              # GitOps Automation
│   └── workflows/
│       └── ci-cd.yml                     # GitHub Actions automated lint, test, build, deploy
│
├── api/                                  # API-First Specifications
│   ├── openapi/
│   │   └── ire_openapi_v1.yaml           # OpenAPI 3.0 REST specification
│   └── proto/
│       └── ire_services.proto            # gRPC Protobuf inter-service definitions
│
├── backend/                              # Python FastAPI Production Backend Skeleton
│   ├── requirements.txt                  # Python dependencies
│   ├── Dockerfile                        # FastAPI backend container definition
│   ├── alembic.ini                       # Alembic migration configuration
│   ├── alembic/                          # Alembic database migration environment
│   └── app/
│       ├── main.py                       # FastAPI entrypoint
│       ├── config.py                     # Pydantic environment configuration
│       ├── core/                         # Auth, DB, Redis, Celery & Security
│       ├── domain/interfaces/            # Pure Abstract Interfaces (IClaimProcessor, IRuleEvaluator)
│       ├── infrastructure/               # Database ORM Models & Celery Background Tasks
│       ├── application/schemas/          # Pydantic DTO schemas
│       ├── api/v1/                       # API Gateway presentation endpoints
│       ├── ai/                           # AI Infrastructure Layer (Gateway, Vector, Agents)
│       ├── ocr/                          # Modular OCR Engine Service
│       ├── rules/                        # Generic Declarative Rule Engine Framework
│       ├── agents/                       # Autonomous Agent Infrastructure Framework
│       └── integration/                  # Enterprise Integration Platform (BaseConnector ABC)
│
├── dashboard/                            # Dark-Themed Control Center SPA
│   ├── index.html                        # Single Page App shell
│   ├── css/styles.css                    # Dark theme design system stylesheet
│   └── js/app.js                         # SPA view router & controller logic
│
├── docs/                                 # Complete Technical Documentation
│   ├── ARCHITECTURE.md                   # System topology & Clean Architecture patterns
│   ├── API_DOCUMENTATION.md              # OpenAPI & gRPC REST/RPC endpoints
│   ├── FOLDER_STRUCTURE.md              # Folder rationale map
│   ├── DATABASE_SCHEMA.md                # PostgreSQL 20-table schema & RLS policies
│   ├── DEPLOYMENT_GUIDE.md               # Docker, K8s, Terraform, Nginx & S3 backup
│   ├── DEVELOPMENT_GUIDE.md              # Local setup & testing instructions
│   ├── CONTRIBUTING.md                   # Code style & Git contribution rules
│   ├── EXTENSION_GUIDE.md                # Extending connectors, vector stores & LLMs
│   └── PLUGIN_GUIDE.md                   # Guide for adding logic without touching infrastructure
│
├── infrastructure/                       # Deployment & Cloud IaC
│   ├── db/
│   │   ├── init.sql                      # Multi-database init script
│   │   └── enterprise_schema.sql         # 20-table PostgreSQL DDL schema with RLS
│   ├── terraform/                        # Infrastructure as Code (AWS VPC, RDS, Redis, S3)
│   ├── k8s/                              # Production Kubernetes Deployment, Service, Ingress, HPA
│   ├── nginx/                            # Nginx Reverse Proxy with TLS 1.3 & Rate Limiting
│   ├── monitoring/                       # Prometheus config & ELK Filebeat log shipper
│   └── scripts/
│       └── backup_recovery.sh            # Automated AES-256 S3 backup & recovery script
│
├── packages/                             # Shared TypeScript Monorepo Libraries
│   ├── shared-domain/                    # Base DDD classes (AggregateRoot, Entity, ValueObject)
│   ├── shared-multitenancy/              # AsyncLocalStorage context propagation
│   ├── shared-events/                    # CloudEvents v1.0 schema & Outbox interfaces
│   ├── shared-rule-engine-contract/      # IRulePlugin & IRuleEvaluator interfaces
│   ├── shared-ai-agent-contract/         # AI tool interfaces & HITL queues
│   ├── shared-logger/                    # OpenTelemetry structured JSON logger
│   └── shared-errors/                    # RFC 7807 problem details error formatters
│
└── services/                             # Decoupled TypeScript Microservices
    ├── tenant-identity-service/          # Multi-tenant onboarding & RBAC
    ├── ingestion-service/                # FHIR R4 & EDI 837 ingestion
    ├── claim-lifecycle-service/          # Claim Aggregate state machine
    ├── reasoning-engine-service/         # AST/WASM Rule Engine runner
    ├── ai-agent-service/                 # Autonomous LLM agent service
    ├── audit-ledger-service/             # Cryptographic SHA-256 audit ledger
    └── notification-event-service/       # Outbox consumer & Webhook/WS dispatcher
```
