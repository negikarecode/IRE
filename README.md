# Insurance Reasoning Engine (IRE) — Platform Architecture & Documentation

Welcome to the **Insurance Reasoning Engine (IRE)** enterprise SaaS platform repository.

IRE is a production-ready, multi-tenant healthcare SaaS platform architecture built on **Clean Architecture**, **Domain-Driven Design (DDD)**, and **Event-Driven Architecture (EDA)**.

> [!IMPORTANT]
> **Strict Platform Boundary (Zero Hardcoded Domain Rules)**:
> The platform infrastructure contains zero hardcoded medical or insurance rules. All domain business logic is decoupled and injected dynamically via **Declarative Rule Engine Plugins**, **WASM modules**, **Autonomous AI Agents**, and **Integration Connectors**.
> Future developers can add domain business logic without modifying core platform microservices or infrastructure code.

---

## 📚 Complete Platform Documentation Sitemap

Detailed guides are available in the [`docs/`](./docs) directory:

- 🏛️ [**Architecture Blueprint**](./docs/ARCHITECTURE.md) — System topology, Clean Architecture, DDD, Event-Driven Outbox pattern, and Multi-Tenancy strategies.
- 🔌 [**API Documentation**](./docs/API_DOCUMENTATION.md) — OpenAPI 3.0 specs, gRPC Protobuf definitions, and FastAPI REST endpoints.
- 📂 [**Folder Structure Rationale**](./docs/FOLDER_STRUCTURE.md) — Complete file & folder map detailing why every directory exists.
- 🗄️ [**Database Infrastructure**](./docs/DATABASE_SCHEMA.md) — 20 production PostgreSQL table definitions, RLS policies, indexes, and triggers.
- 🚀 [**Deployment & DevOps Guide**](./docs/DEPLOYMENT_GUIDE.md) — Docker Compose, Kubernetes manifests, Terraform IaC, Nginx SSL/TLS, and S3 Backup/Recovery scripts.
- 💻 [**Development Guide**](./docs/DEVELOPMENT_GUIDE.md) — Local setup, environment configuration, testing, and debugging workflows.
- 🤝 [**Contribution Guide**](./docs/CONTRIBUTING.md) — Coding conventions, Git workflows, pull request requirements, and linting rules.
- 🧩 [**Extension Guide**](./docs/EXTENSION_GUIDE.md) — How to add new connectors (inheriting from `BaseConnector`), vector stores, and LLM adapters.
- 📦 [**Plugin Guide**](./docs/PLUGIN_GUIDE.md) — **Step-by-step developer guide** on writing and deploying declarative rules and AI tools without touching infrastructure.

---

## ⚡ Quick Start

### 1. Local Monorepo Build (TypeScript & Python)

```bash
# Clone and navigate to workspace
cd /home/aryan/Videos/IRE

# Build TypeScript Monorepo Microservices & Packages
pnpm install
pnpm build

# Setup & Run Python FastAPI Backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### 2. Full-Stack Production Container Deployment

```bash
# Start all microservices, datastores, Kafka, Redis, and FastAPI Backend via Docker Compose
docker-compose -f docker-compose.prod.yml up --build -d
```

---

## 🖥️ Enterprise Control Center Dashboard

Access the dark-themed responsive dashboard at [`dashboard/index.html`](file:///home/aryan/Videos/IRE/dashboard/index.html) or via web server:
- Open `http://localhost:8000/api/v1/docs` for interactive Swagger API documentation.
- Open `dashboard/index.html` in browser for real-time facility, patient, claims, AI engine, and system monitoring telemetry.
