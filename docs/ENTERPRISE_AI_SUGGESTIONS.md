# Enterprise AI Suggestions Panel Manual

This document details the **Enterprise AI Suggestions Panel**, designed with a **GitHub Code Review Comment** user interface for hospital billing staff and revenue cycle auditors.

---

## 🎨 Design Concept: GitHub Code Review Style Finding Cards

```
+---------------------------------------------------------------------------------------------------------------+
| 🤖 ENTERPRISE AI SUGGESTIONS PANEL (2 Active Findings)                                     [Re-run AI]        |
+---------------------------------------------------------------------------------------------------------------+
|                                                                                                               |
| 💬 SUGGESTION #1 (Line Item: CPT 99214)                                                                       |
| ------------------------------------------------------------------------------------------------------------- |
| 🔴 SEVERITY: HIGH RISK (CO-50 Denial)   | 🎯 CONFIDENCE: 98.4% High   | 💰 EST. REVENUE IMPACT: +$450.00           |
|                                                                                                               |
| 📌 ISSUE: Missing Modifier -25 on Evaluation & Management Code CPT 99214                                      |
|                                                                                                               |
| 📝 EXPLANATION:                                                                                               |
| Payer billing rules require Modifier -25 when an E/M service is provided on the same day as a major           |
| surgical procedure (CPT 47562). Submitting without Modifier -25 will trigger an automatic CO-50 denial.        |
|                                                                                                               |
| 🛠️ SUGGESTED FIX:                                                                                             |
| Append Modifier -25 to CPT 99214 and link Operative Report section 3.2.                                        |
|                                                                                                               |
| 📄 AFFECTED DOCUMENTS:                                                                                        |
| - 📄 Operative_Note_Surgical_Receipt.pdf (Section 3.2, Line 42)                                               |
| - 📄 Superbill_Itemized_0728.pdf (Line Item 2)                                                                |
|                                                                                                               |
| [ Accept Suggestion ]  [ Ignore ]  [ Assign to Staff: Sarah J. ▼ ]                                         |
+---------------------------------------------------------------------------------------------------------------+
```

---

## 📋 Comprehensive Finding Card Structure

Each finding card presents non-technical, business-first insights:

1. **`Issue`**: Clear clinical coding or policy discrepancy statement.
2. **`Explanation`**: Business rationale explaining why the claim would trigger a payer denial (e.g. `CO-50`).
3. **`Suggested Fix`**: Exact step-by-step resolution recommendation (e.g. `Append Modifier -25 to CPT 99214`).
4. **`Confidence`**: AI Scrubber confidence rating (e.g. `98.4% High Confidence`).
5. **`Affected Documents`**: Clickable links to specific source chart sections and line numbers.
6. **`Severity`**: Color-coded risk level (`HIGH_RISK`, `MEDIUM_WARNING`, `LOW_INFO`).
7. **`Estimated Revenue Impact`**: Exact financial value protected by resolving the finding (e.g. `+$450.00 At Risk`).

---

## ⚡ 4 Interactive Action Triggers

- **`✓ Accept Suggestion`**: Applies the suggested fix directly to the claim diff, updates status to `RESOLVED`.
- **`✕ Ignore`**: Dismisses the suggestion card with a recorded audit log reason.
- **`Assign to Staff`**: Assigns the issue card to a specific team member (*Sarah J.*, *Dr. Jenkins*, *Robert K.*).
- **`🔄 Re-run AI`**: Triggers the AI Scrubber Engine to re-evaluate after document uploads or manual edits.

---

## 🌐 Live Access

Access the Enterprise AI Suggestions Panel live:
- Open [http://localhost:8080/hospital-workspace.html#ai-suggestions](http://localhost:8080/hospital-workspace.html#ai-suggestions)
