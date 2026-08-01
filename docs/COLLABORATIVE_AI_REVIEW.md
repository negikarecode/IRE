# Collaborative AI Review Workspace Manual

This document details the **Collaborative AI Review Workspace**, styled after **GitHub Pull Requests**, where hospital staff collaborate with AI on claim reviews.

---

## 🎨 Design Concept: GitHub Pull Request Style AI Collaboration

```
+-------------------------------------------------------------------------------------------------------------------------------+
| 🤖 AI REVIEW WORKSPACE — COLLABORATIVE REVIEW SESSION (Claim #CLM-2026-90124)                   [🔄 Re-run AI]                |
| Patient: Jane Doe • Payer: BlueCross BlueShield Choice • Total Billed: $12,900.00 • Status: 2 Active Review Findings          |
+-------------------------------------------------------------+-----------------------------------------------------------------+
| LEFT CANVAS (GitHub PR Claim Diff & Clinical Source)        | RIGHT PANE (GitHub Pull Request Style AI Collaborative Cards)   |
|                                                             |                                                                 |
| 📄 Operative_Note_Surgical_Receipt.pdf [OCR 100%]           | 💬 FINDING CARD #1 (Line Item #2: CPT 99214)                    |
| ----------------------------------------------------------- | --------------------------------------------------------------- |
| [Line Item 1] CPT 47562 — Laparoscopic Cholecystectomy      | 🔴 DENIAL PROBABILITY: 94.8% HIGH | 💰 REVENUE AT RISK: $450.00  |
| Billed: $12,450.00 | Diagnoses: K80.20 (Calculus)           |                                                                 |
| Status: ✓ Verified Compliant                                | 📌 ISSUE: Missing Modifier -25 on Evaluation & Management Code  |
|                                                             |                                                                 |
| [Line Item 2] CPT 99214 — Outpatient Visit (Est Patient)     | 📝 WHY IT MATTERS: Payer rules require Modifier -25 when E/M    |
| Billed: $450.00   | Diagnoses: R07.9 (Chest Pain)          |    is billed on same date as major surgical CPT 47562.         |
| ⚠️ Flagged: Missing Modifier -25                             |                                                                 |
|                                                             | 📑 SUPPORTING EVIDENCE: Operative note section 3.2 documents    |
| 📄 Extracted Metadata Summary:                               |    separate E/M evaluation performed at 08:30 AM before surgery.|
| - Primary Payer: BlueCross BlueShield Choice                |                                                                 |
| - Attached Auth Code: BC-AUTH-99120                         | 📄 AFFECTED DOCUMENTS:                                          |
|                                                             |   - 📄 Operative_Note_Surgical_Receipt.pdf (Section 3.2, Line 42)|
|                                                             |   - 📄 Superbill_Itemized_0728.pdf (Line Item 2)                |
|                                                             |                                                                 |
|                                                             | 🛠️ RECOMMENDED FIX: Append Modifier -25 to CPT 99214.           |
|                                                             |                                                                 |
|                                                             | [ Accept Fix ]  [ Ignore ]  [ Assign: Sarah J. ▼ ]  [ Request MD]|
+-------------------------------------------------------------+-----------------------------------------------------------------+
```

---

## 📋 Comprehensive Finding Card Structure

1. **`Issue`**: Explicit coding mismatch or payer policy violation statement.
2. **`Why It Matters`**: Business rationale explaining why the claim will trigger an automatic payer denial (e.g. `CO-50`).
3. **`Estimated Denial Probability`**: Pre-submission scrubber risk rating (`94.8% HIGH`).
4. **`Revenue At Risk`**: Financial value vulnerable to denial (`$450.00 At Risk`).
5. **`Supporting Evidence`**: Specific clinical excerpt & timestamps from source chart.
6. **`Affected Documents`**: Clickable links to document sections and line numbers.
7. **`Recommended Fix`**: Step-by-step resolution recommendation (`Append Modifier -25 to CPT 99214`).

---

## ⚡ 5 Interactive Action Triggers

- **`✓ Accept Fix`**: Applies fix directly to claim diff, updates status to `RESOLVED`.
- **`✕ Ignore`**: Dismisses finding card with an audit log reason.
- **`Assign to Staff`**: Assigns finding card to a specific billing auditor (*Sarah J.*, *Dr. Jenkins*).
- **`👨‍⚕️ Request MD`**: Sends a clinical clarification inquiry to the treating physician (*Dr. Michael Vance, MD*).
- **`🔄 Re-run AI`**: Re-evaluates AI Scrubber rules and updates findings.

---

## 🌐 Live Access

Access the Collaborative AI Review Workspace live:
- Open [http://localhost:8080/hospital-workspace.html#ai-claim-review](http://localhost:8080/hospital-workspace.html#ai-claim-review)
