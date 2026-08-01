# Enterprise Search Command Palette Manual

This document details the **Linear / Notion Style Command Palette Enterprise Search**, triggered globally via **`Ctrl + K`** or **`Cmd + K`**.

---

## 🔍 Command Palette Search Architecture

```
+-------------------------------------------------------------------------------------------------------------------------------+
|  Top Header Bar...                                                                [🔍 Search Claims, Patients... Ctrl+K]      |
+-------------------------------------------------------------------------------------------------------------------------------+
|                                                                                                                               |
| OVERLAY (GLASSMORPHIC BACKDROP BLUR):                                                                                         |
| +---------------------------------------------------------------------------------------------------------------------------+ |
| | 🔍  Jane Doe                                                                                                 [ Esc ]      | |
| +---------------------------------------------------------------------------------------------------------------------------+ |
| | CATEGORY: CLAIMS                                                                                                          | |
| |  📄 #CLM-2026-90124 — Jane Doe ($12,900.00) • BlueCross BlueShield Choice                         [Press Enter to Open]  | |
| |                                                                                                                           | |
| | CATEGORY: PATIENTS                                                                                                        | |
| |  👤 Jane Doe (MRN-90214) — DOB: 1985-04-12 • Active Coverage: BlueCross                            [Press Enter to Open]  | |
| |                                                                                                                           | |
| | CATEGORY: DOCTORS                                                                                                         | |
| |  👨‍⚕️ Dr. Michael Vance, MD — Attending Surgeon • NPI 1892736102                                   [Press Enter to Open]  | |
| |                                                                                                                           | |
| | CATEGORY: POLICIES                                                                                                        | |
| |  💳 BlueCross Choice Policy — Policy ID: BC-9901238 (Group G-881290)                               [Press Enter to Open]  | |
| |                                                                                                                           | |
| | CATEGORY: DOCUMENTS                                                                                                       | |
| |  📁 Operative_Note_Surgical_Receipt_0728.pdf (2.4 MB) • OCR 100% Extracted                        [Press Enter to Open]  | |
| |                                                                                                                           | |
| | CATEGORY: APPEALS                                                                                                         | |
| |  ⚖️ Case #APP-2026-04 — Aetna CO-50 Appeal ($1,850.00 At Risk)                                    [Press Enter to Open]  | |
| |                                                                                                                           | |
| | CATEGORY: INVOICES                                                                                                        | |
| |  🧾 Invoice #INV-8812 — Billed Encounter $12,900.00 (ENC-8812)                                    [Press Enter to Open]  | |
| |                                                                                                                           | |
| | CATEGORY: INSURANCE COMPANIES                                                                                             | |
| |  🏛️ BlueCross BlueShield Choice — Payer ID: BCBS-9001 (12 Days SLA)                              [Press Enter to Open]  | |
+---------------------------------------------------------------------------------------------------------------------------+ |
+-------------------------------------------------------------------------------------------------------------------------------+
```

---

## ⌨️ Global Keyboard Shortcut & Triggers

- **`Ctrl + K` / `Cmd + K`**: Opens Command Palette instantly from anywhere in the application.
- **`Esc`**: Closes search modal.
- **Header Search Bar Button**: Provides clickable visual trigger in top right header.

---

## 📂 8 Integrated Entity Collections

1. **`Claims`**: Searches claim IDs, billed totals, patient names, and payer names.
2. **`Patients`**: Searches patient names, MRN numbers, DOBs, and active coverage.
3. **`Doctors`**: Searches attending physician names, specialties, and NPI numbers.
4. **`Policies`**: Searches insurance policy IDs, group numbers, copay details.
5. **`Documents`**: Searches clinical chart file names, OCR extraction status, file sizes.
6. **`Appeals`**: Searches appeal case numbers, denial CARC codes, risk dollars.
7. **`Invoices`**: Searches billed encounter invoices and encounter IDs.
8. **`Insurance Companies`**: Searches payer names, payer IDs, payment SLAs.

---

## 🌐 Live Access

Test the Enterprise Search live:
- Open [http://localhost:8080/hospital-workspace.html](http://localhost:8080/hospital-workspace.html) and press **`Ctrl + K`**
