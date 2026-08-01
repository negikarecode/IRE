# Architecture Blueprint & Topology

The **Insurance Reasoning Engine (IRE)** is designed as an enterprise-grade, multi-tenant healthcare SaaS platform architecture.

## High-Level Architecture Topology

```
                                [Client / Frontends / EHRs]
                                             │
                                             ▼
                             [API Gateway Edge Router :8000]
                                             │
                       ┌─────────────────────┴─────────────────────┐
                       ▼                                           ▼
         [Node.js Clean Microservices]                  [Python FastAPI Backend]
        - Tenant Identity Service (:3001)              - Authentication & RBAC
        - Ingestion Service (:3002)                    - Hospital & Patient Index
        - Claim Lifecycle Service (:3003)              - Claims Adjudication Frame
        - Reasoning Engine Service (:3004)             - Document Management & Uploads
        - AI Agent Service (:3005)                     - AI Gateway & Model Registry
        - Audit Ledger Service (:3006)                 - Modular OCR Service Engine
        - Notification Service (:3007)                 - Generic Rule Engine Framework
                                                       - Autonomous Agent Framework
                                                       - Enterprise Integration Platform
                       │                                           │
                       └─────────────────────┬─────────────────────┘
                                             │
                                             ▼
                                  [Data & Event Infrastructure]
                                 - PostgreSQL 16 (RLS Multi-Tenant)
                                 - Redis Cache & PubSub
                                 - Redpanda / Kafka Event Bus
                                 - Qdrant / Vector Store
```

## Core Architectural Patterns

1. **Clean Architecture Layering**: Every microservice and backend module separates concerns strictly:
   - `domain`: Entities, Value Objects, Domain Events, Repository Interfaces.
   - `application`: Commands, Queries, DTOs, Use Cases.
   - `infrastructure`: Database ORM mappings, Kafka producers, Redis caches, HTTP clients.
   - `presentation`: REST Endpoints, OpenAPI schemas, gRPC Handlers.

2. **Domain-Driven Design (DDD)**: Aggregate Roots (`ClaimAggregate`, `TenantAggregate`, `AuditLogAggregate`) enforce transactional consistency boundaries.

3. **Transactional Outbox Pattern**: State mutations and domain events are written to database outbox tables in a single atomic database transaction, ensuring zero event loss across asynchronous event streams.

4. **Multi-Tenant Isolation**: Supports both **Schema-per-Tenant** and **Row-Level Security (RLS)** using `X-Tenant-ID` header injection and `AsyncLocalStorage` execution context.
