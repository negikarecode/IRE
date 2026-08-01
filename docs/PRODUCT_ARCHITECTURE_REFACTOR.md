# Product Architecture & Dual-Application System Manual

This document details the refactored **Two-Application Product Architecture**.

---

## 🏛️ Dual-Application System Topology

```mermaid
graph TD
    User[User Session / Role Access] --> Gateway[App Launcher Gateway / Portal]
    
    Gateway --> App1[1. Internal Platform Console]
    Gateway --> App2[2. Customer Hospital Workspace]

    subgraph App1: Internal Platform Console (IRE Employees Only)
        App1 --> Tenants[All Tenants & Hospitals Directory]
        App1 --> Mon[Platform Monitoring & SLA Metrics]
        App1 --> AIGateway[AI Gateway Token Usage & Costs]
        App1 --> OCRTelemetry[OCR Extraction Usage]
        App1 --> Billing[Billing & Subscriptions]
        App1 --> Support[Customer Support & Incident Queue]
        App1 --> Audit[Cryptographic Audit Trail]
        App1 --> Provision[Tenant Infrastructure Provisioning]
    end

    subgraph App2: Customer Hospital Workspace (Single Hospital SaaS)
        App2 --> Rev[Revenue & Operations Dashboard]
        App2 --> Wards[Facility Beds & Wards Roster]
        App2 --> Patients[Hospital Master Patient Index]
        App2 --> Claims[Operations Claims Stream]
        App2 --> AICheck[AI Claim Review Engine]
        App2 --> Appeals[Appeals & Dispute Center]
        App2 --> Users[Hospital Staff & RBAC]
        App2 --> Analytics[Hospital Performance Analytics]
        App2 --> Settings[Facility Settings & EHR Credentials]
    end

    subgraph Shared Core Backend Infrastructure
        App1 --> Backend[FastAPI Core Backend Engine]
        App2 --> Backend
        Backend --> DB[(PostgreSQL Row-Level Security)]
        Backend --> Redis[(Redis In-Memory Cache)]
        Backend --> Vector[(Qdrant Vector DB)]
        Backend --> Rules[(Rule Reasoning Engine)]
    end
```

---

## 📱 Application Breakdown & Access URLs

| Application | Target Audience | Access Scope | Local URL |
| :--- | :--- | :--- | :--- |
| **Portal Gateway & Launcher** | All Users | Role-Based Launcher | [http://localhost:8080/](http://localhost:8080/) |
| **App 1: Platform Console** | IRE Employees Only | Multi-Tenant (All 148 Hospitals) | [http://localhost:8080/platform-console.html](http://localhost:8080/platform-console.html) |
| **App 2: Hospital Workspace** | Customer Hospital Staff | Single-Tenant (Metro General Hospital Only) | [http://localhost:8080/hospital-workspace.html](http://localhost:8080/hospital-workspace.html) |

---

## 🔐 Security & Tenant Isolation Rules

1. **Platform Console**:
   - Requires `SUPER_ADMIN` or `PLATFORM_OPERATOR` role.
   - Grants multi-tenant visibility across all client organizations, infrastructure health metrics, AI Gateway costs, and global audit logs.

2. **Hospital Workspace**:
   - Scoped strictly to **ONE hospital only** (`Metro General Hospital - NPI: 1982736450`).
   - Strictly enforces Row-Level Security (RLS). Cross-tenant queries or displaying other hospital facilities is impossible by architectural design.
   - Features hospital-specific branding, staff roster, facility wards, patient records, and local AI claim review engines.

3. **Shared Backend Infrastructure**:
   - Both applications interact with the exact same FastAPI backend engine (`port 8000`), share common CSS design system tokens (`css/styles.css`), and utilize standardized API endpoints.
