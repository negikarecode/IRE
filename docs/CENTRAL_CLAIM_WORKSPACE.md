# Central Claim Details Workspace Manual

This document details the **Central Claim Details Workspace**, engineered for 8+ hours of daily intensive use by hospital billing teams, revenue cycle coordinators, and clinical auditors.

---

## 🏛️ 3-Column Workspace Architecture

```
+-------------------------------------------------------------------------------------------------------------------------------+
|  Claim Details Workspace — #CLM-2026-90124 (Jane Doe | MRN-90214 | BlueCross BlueShield)                              |
+------------------------------------+-------------------------------------------+----------------------------------------------+
| LEFT PANEL                         | CENTER PANEL                              | RIGHT PANEL                                  |
| (Patient & Clinical Metadata)      | (Documents, OCR, JSON & Timeline)         | (AI Intelligence & Risk Analysis)            |
|                                    |                                           |                                              |
| 👤 Patient Information             | 📁 Uploaded Documents (3 Files)           | 🤖 AI Findings (2 Total)                     |
| - Jane Doe | MRN-90214 | DOB: 1985     | - Operative_Note_0728.pdf [Preview]       | - [High Risk] Missing Modifier -25           |
|                                    | - Discharge_Summary.pdf [Preview]         | - [Resolved] Prior Auth BC-AUTH-99120        |
| 💳 Insurance Details               |                                           |                                              |
| - BlueCross Choice | BC-9901238    | 👁️ OCR Results                            | 📁 Missing Information                       |
| - Group: G-881290 | Copay: $50.00  | - Text: 100% Extracted | Table: 98.6% Conf  | - [✓] Operative Report                       |
|                                    |                                           | - [✓] Itemized Superbill                     |
| 🏥 Admission Details               | 🌳 Structured JSON                        |                                              |
| - ENC-8812 | Adm: 2026-07-28       | { "claim_id": "CLM-90124", "lines": [...] }| 💰 Revenue Risk & Confidence                 |
|                                    |                                           | - Revenue at Risk: $12,900.00                |
| 👨‍⚕️ Treating Doctor                | 📜 Activity Timeline (Every Change Logged)| - AI Confidence Score: 98.4%                 |
| - Dr. Michael Vance, MD (NPI 1892) | - 10:14: Claim Ingested from EHR          |                                              |
|                                    | - 10:15: OCR Extracted 3 Documents        | 💡 Recommended Fixes                         |
| 🏨 Hospital Stay                   | - 10:16: AI Scrubber Flagged Modifier -25 | 1. Append Modifier -25 to CPT 99214          |
| - 4 Days LOS | Cardiology Room 412 | - 10:18: User Appended Modifier -25       | 2. Submit 837P batch to BlueCross            |
|                                    |                                           |                                              |
| 🩺 Diagnosis (ICD-10)              |                                           |                                              |
| - K80.20 Calculus of Gallbladder   |                                           |                                              |
| - R07.9 Chest Pain                 |                                           |                                              |
|                                    |                                           |                                              |
| 🔬 Procedures (CPT)                |                                           |                                              |
| - CPT 47562 ($12,450.00)           |                                           |                                              |
| - CPT 99214-25 ($450.00)           |                                           |                                              |
+------------------------------------+-------------------------------------------+----------------------------------------------+
| BOTTOM ACTION BAR: [ 💾 Save Draft ] [ 🤖 Run AI Review ] [ ✓ Approve ] [ ⚖️ Generate Appeal ] [ 🚀 Submit Claim (EDI 837) ] |
+-------------------------------------------------------------------------------------------------------------------------------+
```

---

## ⚡ Sticky Bottom Action Bar

The workspace features a high-productivity **Fixed Bottom Action Bar**:

- **`💾 Save Draft`**: Persists claim edits and appends an audit event to the Timeline.
- **`🤖 Run AI Review`**: Triggers real-time AI Scrubber evaluation and updates status tag to `PASSED_AI_SCRUBBER`.
- **`✓ Approve`**: Approves claim for submission (`APPROVED`).
- **`⚖️ Generate Appeal`**: Generates reconsideration appeal package for denied/flagged claims (`APPEAL_GENERATED`).
- **`🚀 Submit Claim (EDI 837)`**: Direct 837P / 837I clearinghouse batch submission (`SUBMITTED_837_EDI`).

---

## 📜 Real-Time Timeline Logging

Every user action, staff edit, AI scrubber run, or clearinghouse submission is automatically recorded and appended into the **Activity Timeline** panel in real-time.

---

## 🌐 Live Access

Access the Central Claim Workspace live:
- Open [http://localhost:8080/hospital-workspace.html#claim-details](http://localhost:8080/hospital-workspace.html#claim-details)
