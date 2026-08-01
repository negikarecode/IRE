# Streamlined Hospital Workspace MVP Architecture Manual

This document details the refactored **Linear / Stripe Style Streamlined Hospital Workspace MVP**.

---

## 🎯 MVP Core Purpose

The MVP is engineered to solve **exactly one problem**:

> **"Help hospital billing teams upload, review, fix and submit insurance claims faster."**

---

## 🏛️ Streamlined 5-Page Architecture

```
+-------------------------------------------------------------------------------------------------------------------------------+
| Metro General Hospital                          [ 🔍 Search Claims, Patients... Ctrl+K ]              Dr. Sarah Jenkins (CFO)|
+-------------------------------------------------------------------------------------------------------------------------------+
| SIDEBAR                 | DASHBOARD (PRIMARY LANDING PAGE)                                                            |
| ----------------------- | ------------------------------------------------------------------------------------------- |
| 📊 Dashboard            | ☁️ HERO UPLOAD CARD (TOP OF DASHBOARD — DRAG & DROP PDF IMMEDIATELY AFTER LOGGING IN)        |
| 📤 Upload Claim         | +-----------------------------------------------------------------------------------------+ |
| 📋 Claims               | |  ☁️ DRAG AND DROP CLINICAL PDF HERE TO START IMMEDIATE AI CLAIM REVIEW                    | |
| ⚖️ Appeals               | |  Drop operative notes, superbills, or discharge charts • Automatic OCR & Scrubber        | |
| ⚙️ Settings              | +-----------------------------------------------------------------------------------------+ |
|                         |                                                                                             |
|                         | 📊 KEY REVENUE STATS                                                                        |
|                         | [ ⏳ 24 Claims Waiting ($420K) ] [ 🚀 86 Claims Ready ($1.42M) ] [ 💰 $1.84M Revenue Pending ]|
|                         |                                                                                             |
|                         | 📋 RECENT CLAIMS REQUIRE ATTENTION TODAY                                                    |
|                         | - #CLM-90124 (Jane Doe) — BlueCross Choice • $12,900.00 • [ Open Claim Review ]             |
|                         | - #CLM-90128 (Robert Smith) — Medicare Part B • $3,450.00 • [ Open Claim Review ]           |
+-------------------------+---------------------------------------------------------------------------------------------+
```

---

## 📋 The 5 Core Pages

1. **`Dashboard`**: Landing page featuring the **Drag & Drop Upload Hero Card** at the top, allowing staff to upload PDFs immediately after logging in, plus 4 essential revenue stats.
2. **`Upload Claim`**: Dedicated document ingestion page.
3. **`Claims`**: Clean claims work queue list.
4. **`Appeals`**: Reconsideration case manager.
5. **`Settings`**: Hospital facility profile and clearinghouse endpoint configuration.

---

## ⚡ Merged "Claim Review" Workflow

AI Review, AI Suggestions, Claim Details, and Document Processing are merged into a single **"Claim Review"** workflow containing:
- Patient & Encounter Metadata
- Attached Document OCR Extracted Text
- AI Scrubber Findings & GitHub PR style action card
- Sticky Bottom Action Bar (`Save Draft`, `Approve`, `Submit Claim EDI 837`)

---

## 🌐 Live Access

Access the Streamlined MVP live:
- Open [http://localhost:8080/hospital-workspace.html#dashboard](http://localhost:8080/hospital-workspace.html#dashboard)
