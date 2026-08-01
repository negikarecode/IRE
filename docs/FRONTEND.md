# Enterprise Control Center Frontend Manual

This document details the production-ready **Enterprise Frontend Control Center**.

> [!IMPORTANT]
> **Strict Policy**:
> The UI includes **ZERO insurance widgets** (zero insurance policy widgets, zero insurance claims adjudication widgets). All operational views showcase generic SaaS enterprise platform management, facility monitoring, AI gateway telemetry, and integration pipeline monitoring.

---

## 🎨 Design System & UX Principles

- **Dark Theme Palette**: Deep dark canvas (`#090d16`), slate secondary background (`#0f172a`), glassmorphic card overlays (`rgba(30, 41, 59, 0.7)`), subtle glowing borders, and vibrant accent colors (cyan `#00f2fe`, purple `#a855f7`, green `#10b981`, blue `#3b82f6`).
- **Typography**: Google Fonts Inter for clean UI copy & JetBrains Mono for system log terminals and code snippets.
- **Responsiveness**: 100% responsive layout with fixed/collapsible sidebar navigation, sticky blurred top bar, and auto-fit KPI grids.
- **Reusable Components**:
  - `StatCard`: Glassmorphic KPI cards with trend indicators.
  - `DataTable`: Styled data tables with status badges and action buttons.
  - `StatusBadge`: Color-coded pill badges (`ACTIVE`, `VERIFIED`, `RUNNING`, `HEALTHY`).
  - `TerminalBox`: Dark code/log terminal view with syntax highlighting.
  - `TabContainer`: Dynamic tab-based routing without full page reloads.

---

## 🖥️ Platform Dashboard Views

1. 🏥 **Hospital Dashboard** (`#hospitals`)
   - KPI cards for connected hospitals, bed capacity, EHR probes (EPIC/Cerner integration status), and daily ingestion streams.
   - Interactive table of registered hospital facilities with NPI numbers, facility types, and status.

2. 👥 **Patients Dashboard** (`#patients`)
   - Master Patient Index (MPI) metrics: Total registered patients, active inpatient/outpatient admissions, and identity matching rates.
   - Patient demographic table with MRN search and record links.

3. ⚡ **Operations Claims Pipeline Dashboard** (`#claims`)
   - Operational service request pipeline metrics: Daily throughput, automated verification rate, and escalated audit queue.
   - Real-time operations stream table displaying claim/task references, values, verification status, and confidence scores.

4. 🤖 **AI & Agents Dashboard** (`#ai-engine`)
   - LLM Gateway telemetry across OpenAI, Google Gemini, Anthropic Claude, and Local Llama3 (vLLM).
   - Active Autonomous ReAct Agents task queue status, AI Cache hit ratio ($84.2\%$), and token latency breakdown.

5. 📊 **Analytics Dashboard** (`#analytics`)
   - System performance, API request throughput, and latency distribution charts across all microservices and datastores.

6. 🛡️ **Admin Panel** (`#admin`)
   - Role-Based Access Control (RBAC) matrix defining permissions for `SUPER_ADMIN`, `AUDITOR`, and `DEVELOPER` roles across tenants.

7. 📜 **Audit Ledger** (`#logs`)
   - Cryptographic SHA-256 immutable audit trail terminal output detailing platform events, rule evaluations, and agent completions.

8. 🔔 **Notifications** (`#notifications`)
   - Real-time event dispatch feed: Webhook execution logs, AI Gateway provider failover alerts, and DLQ replay notifications.

9. 📄 **Reports** (`#reports`)
   - PDF/CSV generation and download center for daily system audit summaries.

10. ⚙️ **Settings** (`#settings`)
    - Tenant API keys, domain policy guardrail status, and security configuration.

---

## 🚀 How to Access

Access the dashboard directly in your browser:
- Open [`dashboard/index.html`](file:///home/aryan/Videos/IRE/dashboard/index.html) in any web browser.
