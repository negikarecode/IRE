# Patient 360° Master Profile Manual

This document details the **Patient 360° Master Profile**, serving as the single source of truth for patient clinical, billing, coding, and denial history.

---

## 🏛️ Patient 360° Single Source Architecture

```
+-------------------------------------------------------------------------------------------------------------------------------+
| 👤 PATIENT 360° MASTER PROFILE — JANE DOE (MRN-90214)                                                                         |
| DOB: 1985-04-12 (39 yrs) • Primary Payer: BlueCross BlueShield Choice • Lifetime Revenue: $48,200.00 ($42,500 Paid)           |
+-------------------------------------------------------------+-----------------------------------------------------------------+
| LEFT PANEL (360° Demographics, Insurance, Revenue & Docs)   | RIGHT PANEL (Unified 360° Timeline & Clinical/Claim History)    |
|                                                             |                                                                 |
| 👤 DEMOGRAPHICS & CONTACT                                   | 📜 UNIFIED 360° CHRONOLOGICAL PATIENT TIMELINE                  |
| - Full Name: Jane Doe \| Gender: Female                     | --------------------------------------------------------------- |
| - Phone: (555) 234-5678 \| Emergency: John Doe (Spouse)    | - 2026-08-01 10:24 AM: Claim #CLM-2026-90124 Submitted ($12.9k) |
| - Address: 742 Evergreen Terrace, Metro City                | - 2026-07-28 08:30 AM: Inpatient Admission (ENC-8812, Room 412) |
|                                                             | - 2026-07-28 09:15 AM: Operative_Note_0728.pdf Uploaded & OCR   |
| 💳 INSURANCE & ELIGIBILITY                                  | - 2026-07-29 11:00 AM: AI Scrubber Flagged Missing Mod -25       |
| - Primary: BlueCross Choice (BC-9901238, Group G-881290)    | - 2026-07-30 02:15 PM: Mod -25 Appended by Sarah J.             |
| - Copay: $50.00 \| Deductible: $0.00                        | - 2026-07-15 01:00 PM: Past Claim #CLM-77019 Billed ($1,850.00) |
|                                                             | - 2026-07-28 04:30 PM: Aetna Issued Denial CO-50                |
| 💰 REVENUE HISTORY & LIFETIME METRICS                       |                                                                 |
| - Total Lifetime Billed: $48,200.00                         | 🏥 ADMISSIONS & ENCOUNTERS                                      |
| - Total Cash Collected: $42,500.00                           | - ENC-8812 (2026-07-28 to 2026-08-01): Cardiology Ward          |
| - Current Revenue at Risk: $1,850.00 (Aetna Appeal)         | - ENC-7410 (2026-04-10 to 2026-04-12): Outpatient Surgery       |
|                                                             |                                                                 |
| 📁 CLINICAL & CLAIMS DOCUMENTS                              | 🤖 AI FINDINGS & PAST DENIALS                                   |
| - 📄 Operative_Note_0728.pdf [Preview]                      | - [Resolved] Modifier -25 Flagged on CPT 99214                  |
| - 📄 Discharge_Summary.pdf [Preview]                        | - [Active Appeal] CARC CO-50 Denial on CPT 47562 ($1,850.00)    |
| - 📄 Lab_Panel_Bloodwork.pdf [Preview]                      |                                                                 |
+-------------------------------------------------------------+-----------------------------------------------------------------+
```

---

## 📋 10 Core Profile Modules

1. **`Demographics`**: Full legal name, MRN, DOB, Gender, Phone, Address, Emergency Contact.
2. **`Admissions`**: Inpatient & outpatient encounter histories (`ENC-8812`, `ENC-7410`).
3. **`Timeline`**: Unified 360-degree chronological activity feed spanning admissions, document OCR, AI scrubber runs, staff edits, EDI submissions, and denial appeals.
4. **`Claims`**: Lifetime encounter claim billing records ($48,200.00 total).
5. **`Insurance`**: Primary payer policy details (`BC-9901238`, Group `G-881290`).
6. **`Clinical Documents`**: Ingested operative notes, lab reports, discharge summaries.
7. **`AI Findings`**: Pre-submission scrubber compliance flags and resolutions.
8. **`Past Denials`**: Historical denial CARC codes (`CO-50`) and appeal recovery progress.
9. **`Revenue History`**: Lifetime cash collected ($42,500.00 / 88.1% recovery rate).
10. **`Documents Repository`**: Inline document viewer & download center.

---

## 🌐 Live Access

Access the Patient 360° Profile live:
- Open [http://localhost:8080/hospital-workspace.html#patients](http://localhost:8080/hospital-workspace.html#patients)
