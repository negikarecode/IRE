# Operational Command Center Manual

This document details the **Operational Command Center**, which replaces all static charts with a 100% interactive, real-time command dashboard.

---

## ⚡ 100% Interactive Command Center Architecture

```
+-------------------------------------------------------------------------------------------------------------------------------+
| ⚡ OPERATIONAL COMMAND CENTER — METRO GENERAL HOSPITAL                               [⚡ Live Stream Active]                  |
+-------------------------------------------------------------------------------------------------------------------------------+
| TOP OPERATIONAL KPIS (All Clickable -> Filter Work Queue)                                                                     |
| +---------------------+ +---------------------+ +---------------------+ +---------------------+ +---------------------+ +---+ |
| | ⏳ Claims Waiting   | | 🚀 Claims Ready     | | ⚠️ Claims Delayed   | | 💰 Revenue Waiting  | | 🛡️ Revenue Saved    | | ⏱️| |
| | 24 Claims ($420K)   | | 86 Claims ($1.42M)  | | 4 Claims ($180K)    | | $1.84M Pending      | | $412K by AI         | |1.8| |
| +---------------------+ +---------------------+ +---------------------+ +---------------------+ +---------------------+ +---+ |
+-------------------------------------------------------------------------------------------------------------------------------+
| BELOW KPIS COMMAND CENTER GRID (Clickable Widgets)                                                                            |
|                                                                                                                               |
| 📥 TODAY'S WORK QUEUE (Widget)                     | 🚨 CRITICAL CLAIMS (Widget)                                               |
| - Claim #CLM-90124 ($12,900) Needs AI Review      | - Claim #CLM-90130 ($18,200) High Risk • 4h to deadline                  |
| - Claim #CLM-90128 ($3,450) Missing Docs          | - Claim #CLM-77019 ($1,850) Appeal Deadline 12h                          |
| [Click -> Open Filtered Work Queue]               | [Click -> Open Critical Queue]                                            |
| --------------------------------------------------+-------------------------------------------------------------------------- |
| 👨‍⚕️ CLAIMS WAITING ON DOCTOR                     | 🏛️ CLAIMS WAITING ON INSURANCE                                           |
| - 4 Claims Pending MD Sign-off ($42,000)          | - 18 Prior Auths Pending Adjudication ($240,000)                          |
| [Click -> Open Needs Doctor Queue]                | [Click -> Open Insurance Queue]                                           |
| --------------------------------------------------+-------------------------------------------------------------------------- |
| 📄 CLAIMS MISSING DOCUMENTS                       | ⚡ REAL-TIME ACTIVITY FEED                                               |
| - 8 Claims Missing Operative Notes / EOBs         | - 10:24 AM: Sarah J. submitted Batch #837-99210                           |
| [Click -> Open Missing Docs Queue]                | - 10:22 AM: AI Scrubber prevented CO-50 denial on #CLM-90124              |
| --------------------------------------------------+-------------------------------------------------------------------------- |
| ⏰ UPCOMING DEADLINES                                                                                                          |
| - Appeal #APP-2026-04 (Aetna): 12 Hours Left ($1,850.00)                                                                      |
| - Prior Auth #PA-9013 (Medicare): 24 Hours Left ($3,450.00)                                                                   |
+-------------------------------------------------------------------------------------------------------------------------------+
```

---

## 📊 6 Top Operational KPIs & Interactive Actions

Every KPI card is clickable and immediately routes to the filtered **Work Queue** (`#work-queue`):

1. **`⏳ Claims Waiting`**: 24 Claims ($420K value) awaiting scrubber review.
2. **`🚀 Claims Ready`**: 86 Claims ($1.42M EDI 837 compliant) ready for clearinghouse submission.
3. **`⚠️ Claims Delayed`**: 4 Claims ($180K value) delayed > 48 hours.
4. **`💰 Revenue Waiting`**: $1.84M pending payer adjudication.
5. **`🛡️ Revenue Saved by AI`**: $412K saved from coding error denials.
6. **`⏱️ Avg Processing Time`**: 1.8 hours per claim (-0.6h vs industry benchmark).

---

## 🛠️ Interactive Command Center Widgets

- **`📥 Today's Work Queue`**: Quick preview of today's claims requiring action.
- **`🚨 Critical Claims`**: Expiring high-risk claims near deadline.
- **`👨‍⚕️ Claims Waiting on Doctor`**: Claims requiring physician clinical sign-off.
- **`🏛️ Claims Waiting on Insurance`**: Claims pending prior auth or 835 remittance.
- **`📄 Claims Missing Documents`**: Claims missing superbills or operative reports.
- **`⚡ Real-time Activity Feed`**: Live operational stream of clearinghouse submissions and scrubber runs.
- **`⏰ Upcoming Deadlines`**: Countdown timers for expiring appeals and prior auths.

---

## 🌐 Live Access

Access the Operational Command Center live:
- Open [http://localhost:8080/hospital-workspace.html#dashboard](http://localhost:8080/hospital-workspace.html#dashboard)
