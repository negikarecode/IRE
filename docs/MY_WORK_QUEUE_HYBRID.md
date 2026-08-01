# My Work Queue — Workflow-Driven Landing Page Manual

This document details **"My Work Queue"**, the primary workflow-driven landing page for the Hospital Workspace SaaS product.

---

## 🏛️ Executive Workflow Purpose

When a hospital billing executive, revenue manager, or coder logs in, they are immediately directed to **"My Work Queue"**, which answers the core question:

> **"What should I work on right now?"**

---

## 📊 8-Column Kanban + Table Hybrid Layout

The interface features a segmented control allowing one-click toggling between **⏹️ Kanban Board** mode and **☰ Table List** mode:

```
+-------------------------------------------------------------------------------------------------------------------------------+
|  My Work Queue — Hospital Revenue Intelligence                        [View: ⏹️ Kanban | ☰ Table]   [Filter: All Payers ▼] |
|  "What should I work on right now?" — 84 Claims Require Action Today ($1.84M Total Revenue at Risk)                           |
+-------------------------------------------------------------------------------------------------------------------------------+
|                                                                                                                               |
| [1. Needs AI Review]   [2. Missing Docs]   [3. Needs Doctor]   [4. Ready to Submit]   [5. Submitted]   [6. Denied] ...       |
| (12 Claims)            (8 Claims)          (4 Claims)          (86 Claims)            (42 Claims)      (6 Claims)             |
| --------------------   -----------------   -----------------   --------------------   --------------   -----------            |
| 🎴 Claim #CLM-90124    🎴 Claim #CLM-90128  🎴 Claim #CLM-90130  🎴 Claim #CLM-88012    🎴 Claim #CLM...  🎴 Claim #CLM...       |
| Jane Doe               Robert Smith        Michael Vance       Jane Doe               ...              ...                    |
| BlueCross Choice       Medicare Part B     Aetna               BlueCross              ...              ...                    |
| Amount: $12,900.00     Amount: $3,450.00   Amount: $18,200.00  Amount: $2,450.00      ...              ...                    |
| Risk: HIGH RISK        Risk: MEDIUM        Risk: HIGH RISK     Risk: LOW RISK         ...              ...                    |
| AI Conf: 98.4%         AI Conf: 84.0%      AI Conf: 91.2%      AI Conf: 99.8%         ...              ...                    |
| Updated: 10m ago       Updated: 25m ago    Updated: 1h ago     Updated: 2h ago        ...              ...                    |
| At Risk: $12,900.00    At Risk: $3,450.00  At Risk: $18,200.00  At Risk: $0.00         ...              ...                    |
| [Open] [Run AI]        [Open] [Assign]     [Open] [Assign]     [Open] [Submit]        ...              ...                    |
+-------------------------------------------------------------------------------------------------------------------------------+
```

---

## 🎴 Claim Card & Table Data Schema

Every claim card displays:

- **`Claim ID`**: Unique claim reference (`#CLM-90124`).
- **`Patient Name`**: Full patient name (`Jane Doe`).
- **`Insurance Company`**: Primary payer (`BlueCross BlueShield Choice`).
- **`Claim Amount`**: Billed encounter total (`$12,900.00`).
- **`Current Stage`**: Stage column (`Needs AI Review`, `Missing Documents`, `Ready to Submit`, etc.).
- **`Risk Level`**: Color-coded risk badge (`HIGH_RISK`, `MEDIUM`, `LOW_RISK`).
- **`AI Confidence`**: Pre-submission scrubber confidence rating (`98.4%`).
- **`Last Updated`**: Recency timestamp (`10m ago`).
- **`Estimated Revenue at Risk`**: Dollar value vulnerable to denial (`$12,900.00`).

---

## ⚡ Card Action Triggers

- **`Open Claim`**: Navigates directly to the Claim Details workspace (`#claim-details`).
- **`Run AI Review`**: Triggers real-time AI Scrubber evaluation.
- **`Assign`**: Assigns claim card to a specific billing auditor or physician.
- **`Submit`**: Transmits EDI 837 batch to clearinghouse (`#ready-to-submit`).
- **`Appeal`**: Initiates reconsideration case (`#appeals`).

---

## 🌐 Live Access

Access "My Work Queue" live:
- Open [http://localhost:8080/hospital-workspace.html#work-queue](http://localhost:8080/hospital-workspace.html#work-queue)
