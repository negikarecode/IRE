# Appeals Case Manager Manual

This document details the **Appeals & Reconsideration Case Manager**, replacing flat appeal lists with a case management workspace.

---

## 🏛️ Appeals Case Management Architecture

```
+-------------------------------------------------------------------------------------------------------------------------------+
| ⚖️ APPEALS & RECONSIDERATION CASE MANAGER (Case #APP-2026-04 — Claim #CLM-77019)                                            |
| Insurer: Aetna Healthcare Choice • Denial Code: CO-50 (Non-covered service) • Deadline: ⏰ 12 Hours Left ($1,850.00 At Risk)  |
+-------------------------------------------------------------------------------------------------------------------------------+
| VISUAL APPEAL PROGRESS STEPPER:                                                                                               |
| [✓ Denied (CO-50)] ➔ [✓ AI Draft Generated] ➔ [✓ Evidence Attached] ➔ [⚡ Submitted to Payer] ➔ [⏳ Payer Review] ➔ [Overturned]|
+-------------------------------------------------------------+-----------------------------------------------------------------+
| LEFT CASE DATA & EVIDENCE PANEL                             | RIGHT AI APPEAL DRAFT & CASE MANAGEMENT PANE                    |
|                                                             |                                                                 |
| 🔴 DENIAL DETAILS & REASON                                  | 🤖 AI RECONSIDERATION LETTER DRAFT                              |
| - Denial Code: CO-50 (Lack of Medical Necessity)            | --------------------------------------------------------------- |
| - Denial Amount: $1,850.00                                  | "To: Aetna Provider Appeals Department                         |
| - Service Date: 2026-07-15                                  |  RE: Formal Reconsideration Appeal for Claim #CLM-77019         |
|                                                             |  Patient: Jane Doe | Policy ID: AET-9912038                     |
| 📜 APPEAL TIMELINE                                          |                                                                 |
| - 2026-07-28: Claim #CLM-77019 denied by Aetna (CO-50)     |  Dear Appeals Committee,                                        |
| - 2026-07-29: AI Appeal Generator drafted reconsideration   |  We respectfully appeal the CO-50 denial... Operative note      |
| - 2026-07-30: Operative Note Section 3.2 attached          |  Section 3.2 confirms laparoscopic approach was medically       |
| - 2026-08-01: Reconsideration package ready for submission. |  necessary per Clinical Policy Guidelines §4.2..."              |
|                                                             |                                                                 |
| 📁 SUPPORTING DOCUMENTS (2 Attached)                        | 📁 MISSING EVIDENCE CHECKLIST                                   |
| - 📄 Operative_Note_Section_3.2.pdf [Attached]              | - [✓] Clinical Chart Notes (Attached)                           |
| - 📄 Physician_Peer_Review_Citation.pdf [Attached]          | - [✓] Operative Report (Attached)                               |
|                                                             | - [!] Attending Physician Signature (Verified)                  |
|                                                             |                                                                 |
|                                                             | BUTTONS:                                                        |
|                                                             | [ Generate AI Appeal ] [ Edit ] [ Preview PDF ] [ Submit ] [ Track]|
+-------------------------------------------------------------+-----------------------------------------------------------------+
```

---

## 📈 Visual Appeal Stepper Stages

1. `1. Claim Denied (CO-50)`
2. `2. AI Draft Generated`
3. `3. Evidence Attached`
4. `4. Submitted to Payer`
5. `5. Payer Review`
6. `6. Overturned & Paid`

---

## ⚡ 5 Interactive Case Action Triggers

- **`🤖 Generate AI Appeal`**: Triggers real-time AI reconsideration letter generator.
- **`✏️ Edit Letter`**: Makes the letter draft paper interactive for inline staff edits.
- **`📄 Preview PDF`**: Renders formatted PDF reconsideration packet preview.
- **`🚀 Submit Appeal`**: Transmits appeal package to Aetna clearinghouse portal and updates progress stepper to `Submitted to Payer`.
- **`📡 Track Payer Status`**: Checks real-time clearinghouse portal adjudication SLA.

---

## 🌐 Live Access

Access the Appeals Case Manager live:
- Open [http://localhost:8080/hospital-workspace.html#appeals](http://localhost:8080/hospital-workspace.html#appeals)
