# IRE Platform Console Manual (Internal Employees Only)

This document details the **IRE Platform Console**, the internal administration application used exclusively by internal IRE engineers, platform operators, and commercial support staff.

---

## 🏛️ Application Scope & Security Boundary

> [!IMPORTANT]
> The **IRE Platform Console** is strictly restricted to internal employees (`PLATFORM_OPERATOR`, `SUPER_ADMIN`). None of these pages or developer telemetry screens are ever exposed to customer hospital workspaces.

---

## 📋 Comprehensive 13-Page Navigation Structure

| # | Page / Section | Description |
| :-: | :--- | :--- |
| **1** | **Hospital Management** | Multi-tenant directory of all 148 connected hospital facilities across client tenants. |
| **2** | **Tenant Management** | Onboarding new client organizations, configuring RLS PostgreSQL / dedicated DB isolation policies. |
| **3** | **AI Gateway** | Multi-provider LLM adapter gateway routing (OpenAI, Gemini, Claude, Local Ollama). |
| **4** | **Provider Health** | Real-time API latency probes (180ms - 210ms), uptime checks, and fallback chain triggers. |
| **5** | **LLM Costs** | Daily token ingestion (42.8M tokens) and financial cost accounting ($778.00 daily spend). |
| **6** | **OCR Usage** | Modular OCR document processing throughput (124,500 pages/day) and table matrix extractions. |
| **7** | **Platform Analytics** | Event stream throughput (4.8M events/day) and API P99 latency (42ms). |
| **8** | **Infrastructure Monitoring** | Health monitoring for 7 core microservices and EKS autoscale cluster nodes. |
| **9** | **Audit Ledger** | Cryptographic SHA-256 event audit trail across all enterprise tenants. |
| **10** | **Subscriptions** | Enterprise tenant subscription tiers, ARR tracking ($2.4M ARR), and 99.4% NRR. |
| **11** | **Customer Support** | Customer support ticket queue, SLA breach alerts, and escalation tracking. |
| **12** | **Billing** | Monthly enterprise invoicing, usage-based overages, and payment collection status. |
| **13** | **Developer Tools** | Founder A Business Logic SDK extension point registry, plugin discovery, and Swagger API docs. |

---

## 🌐 Live Access

Access the IRE Platform Console live:
- Open [http://localhost:8080/platform-console.html](http://localhost:8080/platform-console.html)
