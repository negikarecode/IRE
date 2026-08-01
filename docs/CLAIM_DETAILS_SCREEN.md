# Claim Details Screen Specification

This document details the **Claim Details Screen**, the primary workspace screen where hospital billing staff, revenue coordinators, and clinical auditors spend most of their workday.

---

## 🏛️ Screen Layout Architecture

The Claim Details screen features a **Top Action Toolbar** and a **2-Column Split Grid**:

```
+---------------------------------------------------------------------------------------------------------------+
|  Claim Details: #CLM-2026-90124 (Jane Doe | MRN-90214 | BlueCross)      [Save Draft] [Run AI] [Approve] [Send] [Escalate] |
+---------------------------------------------------------------------------------------------------------------+
| LEFT COLUMN (Primary File & Data Panels)                    | RIGHT COLUMN (Intelligence & Activity)          |
|                                                             |                                                 |
| 👤 PATIENT INFORMATION                                      | 📊 RISK SUMMARY                                 |
| - Name: Jane Doe  | MRN: MRN-90214  | DOB: 1985-04-12         | - Denial Risk: 1.6% (LOW RISK)                  |
| - Gender: Female  | Phone: (555) 234-5678                   | - Projected Recovery: $12,900.00 (98.4%)        |
| - Admission: 2026-07-28 | Encounter: Inpatient Surgical     |                                                 |
|                                                             | 🤖 AI FINDINGS                                  |
| 💳 INSURANCE INFORMATION                                    | - [High Risk] Modifier -25 Missing on CPT 99214 |
| - Primary Payer: BlueCross BlueShield Choice                | - [Resolved] Prior Auth BC-AUTH-99120 Attached  |
| - Policy ID: BC-9901238 | Group #: G-881290                 |                                                 |
| - Subscriber: Self | Auth Code: BC-AUTH-99120                | 📁 MISSING DOCUMENTS CHECKLIST                  |
| - Copay: $50.00 | Remaining Deductible: $0.00               | - [✓] Operative Report (Attached)               |
|                                                             | - [✓] Superbill / Itemized Receipt (Attached)   |
| 📁 UPLOADED DOCUMENTS (3)                                   | - [!] Physician Order Form (Optional)           |
| - 📄 Operative_Note_Surgical_Receipt.pdf [View]             |                                                 |
| - 📄 Discharge_Summary_Jane_Doe.pdf [View]                  | 💡 RECOMMENDATIONS                              |
| - 📄 Lab_Panel_Bloodwork.pdf [View]                         | 1. Append Modifier -25 to CPT 99214.            |
|                                                             | 2. Submit 837P EDI batch to BlueCross clearinghouse.|
| 📜 TIMELINE                                                 |                                                 |
| - 10:14 AM: Claim Created by Coder Sarah                    | 💬 CLAIM NOTES                                  |
| - 10:15 AM: OCR Extracted 3 Documents (100% Conf.)          | - [Sarah J.]: Prior Auth verified with payer.   |
| - 10:16 AM: AI Scrubber Identified Missing Modifier -25     | - [Dr. Jenkins]: Approved for submission.       |
| - 10:18 AM: Modifier -25 Appended by User                   |                                                 |
|                                                             | 📜 PATIENT CLAIM HISTORY (3 Past Claims)        |
|                                                             | - CLM-2025-4012: $4,200.00 (PAID IN FULL)       |
|                                                             | - CLM-2025-1102: $1,850.00 (PAID IN FULL)       |
+-------------------------------------------------------------+-------------------------------------------------+
```

---

## ⚡ Primary Action Toolbar

| Button | Target Action | Behavior |
| :--- | :--- | :--- |
| **💾 Save Draft** | Internal state persistence | Saves current edits, displays confirmation toast |
| **🤖 Run AI Review** | Automated CCI scrubber run | Evaluates coding rules, updates status to `PASSED_AI_SCRUBBER` |
| **✓ Approve** | Auditor sign-off | Approves claim for submission, updates status to `APPROVED` |
| **🚀 Send to Insurance** | EDI 837 clearinghouse batch | Transmits claim to BlueCross clearinghouse (`SUBMITTED_837_EDI`) |
| **⚠️ Escalate** | Auditor escalation | Flags claim for senior audit review (`ESCALATED_AUDIT`) |

---

## 📋 Comprehensive 10-Panel Breakdown

1. **Patient Information**: Full patient demographics (MRN, Name, DOB, Phone, Gender, Admission Date, Encounter Type).
2. **Insurance Information**: Primary Payer, Policy ID, Group Number, Subscriber Name, Prior Auth Code, Copay / Deductible.
3. **Uploaded Documents**: 3 attached clinical files (Operative Report, Discharge Summary, Lab Panel) with document view triggers.
4. **Timeline**: Complete audit trail (Ingestion -> OCR Extraction -> AI Scrubber -> User Fixes -> Approval).
5. **Risk Summary**: Denial Probability (1.6%), Projected Payment Yield ($12,900.00), EDI 837 Validation status.
6. **AI Findings**: Coding compliance findings, modifier validation, prior auth matches.
7. **Missing Documents Checklist**: Verification of attached required documents.
8. **Recommendations**: Actionable step-by-step guidance for hospital staff.
9. **Claim Notes**: Collaborative internal staff discussion thread with real-time posting.
10. **Patient History**: Historical claim records for this patient with past payment outcomes.

---

## 🌐 Live Access

Access the Claim Details screen live:
- Open [http://localhost:8080/hospital-workspace.html#claim-details](http://localhost:8080/hospital-workspace.html#claim-details)
