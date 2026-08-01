# AI Claim Review Workspace Specification

This document details the **AI Claim Review Workspace**, the main screen of the Hospital Revenue Intelligence SaaS product.

---

## 🎨 UX Design Concept: "GitHub Pull Requests Meets Figma Comments"

```
+-------------------------------------------------------------------------------------------------------+
|  AI Claim Review Workspace — Claim Ref: #CLM-2026-90124 (Patient: Jane Doe | Payer: BlueCross)        |
+-------------------------------------------------------------------------------------------------------+
|  [1. Upload] -> [2. OCR] -> [3. Extract Data] -> [4. AI Review] -> [5. Issues (2)] -> [6. Fixes] -> [7. Approve] -> [8. Submit] |
+-------------------------------------------------------------+-----------------------------------------+
| LEFT CANVAS (GitHub PR Style Claim & Clinical Diff)          | RIGHT PANE (Figma Comment Annotations)  |
|                                                             |                                         |
| 📄 Document: Operative_Note_Surgical_Receipt.pdf             | 💬 AI Annotation #1 (Line Item 2)       |
|                                                             | 🔴 HIGH RISK: Missing Modifier -25      |
| [Line Item 1] CPT 47562 — Laparoscopic Cholecystectomy      | "CPT 99214 evaluated on same date as    |
| Billed: $12,450.00 | Diagnoses: K80.20                       |  surgical procedure CPT 47562 without   |
| Status: ✓ Verified Compliant                                |  Modifier -25 will trigger CO-50 denial."|
|                                                             | 🛠️ Suggested Fix:                       |
| [Line Item 2] CPT 99214 — Outpatient Visit                  | [ Apply Fix: Append Modifier -25 ]       |
| Billed: $450.00   | Diagnoses: R07.9 (Chest Pain)          | --------------------------------------- |
| ⚠️ Issue: E/M code without Modifier -25                      | 💬 AI Annotation #2 (Diagnosis Code)    |
|                                                             | 🟡 WARNING: Prior Auth Required         |
| 📄 Extracted Data Summary:                                   | [ Apply Fix: Attach PA Code BC-99120 ]  |
| - Total Billed Charge: $12,900.00                           | --------------------------------------- |
| - Primary Payer: BlueCross BlueShield Choice                | [ APPROVE CLAIM ]  [ SUBMIT TO EDI 837 ]|
+-------------------------------------------------------------+-----------------------------------------+
```

---

## 🔄 End-to-End Stepper Workflow Pipeline

```
Upload Documents ➔ OCR Engine ➔ Extract Data ➔ AI Review ➔ Issues Found ➔ Suggested Fixes ➔ Approve ➔ Submit (EDI 837)
```

1. **Upload Documents**: Clinical charts, operative notes, superbills, and EOBs ingested.
2. **OCR Engine**: 100% text, layout, and handwriting extractions.
3. **Extract Data**: Procedure CPT codes, ICD-10 diagnosis codes, line item charges.
4. **AI Review**: Payer policy rules, CCI edit scrubbers, prior auth verification.
5. **Issues Found**: High-density findings flagged with CARC/RARC denial prevention rationale.
6. **Suggested Fixes**: One-click **"Apply Suggested Fix"** buttons update the claim diff canvas in real-time.
7. **Approve**: One-click claim approval once all findings are resolved.
8. **Submit (EDI 837)**: Direct 837P / 837I clearinghouse batch submission.

> [!IMPORTANT]
> **Zero Prompts or System Logs**:
> The user NEVER sees AI prompt templates, system instructions, or raw JSON. Only clean, actionable business findings, financial impacts, and one-click fix buttons.

---

## 🌐 Live Access

Access the main screen live in your browser:
- Open [http://localhost:8080/hospital-workspace.html#ai-claim-review](http://localhost:8080/hospital-workspace.html#ai-claim-review)
