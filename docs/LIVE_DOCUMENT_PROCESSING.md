# Live Document Processing Center Manual

This document details the **Live Document Processing Center**, featuring 7-stage live ingestion status tracking and interactive document inspection drawers.

---

## 🏛️ Live 7-Stage Ingestion Pipeline Architecture

```
+-------------------------------------------------------------------------------------------------------------------------------+
| 📥 LIVE DOCUMENT PROCESSING CENTER — METRO GENERAL HOSPITAL                                                                   |
| Real-Time Clinical Ingestion Pipeline • 3 Active Documents In Process • 100% Scrubber Validation                              |
+-------------------------------------------------------------------------------------------------------------------------------+
| 7-STAGE LIVE INGESTION PIPELINE:                                                                                              |
| [1. Queued] ➔ [2. Uploading] ➔ [3. OCR] ➔ [4. Extracting] ➔ [5. Structuring] ➔ [6. AI Review] ➔ [7. Completed]                |
+-------------------------------------------------------------------------------------------------------------------------------+
| CLICKABLE LIVE DOCUMENT PROCESSING QUEUE:                                                                                     |
|                                                                                                                               |
| 🎴 Document 1: Operative_Note_Surgical_Receipt_0728.pdf (2.4 MB)                                                             |
| Status: [ 7. Completed ] • Confidence: 99.2% • Errors: 0 • Warnings: 1 (Modifier -25 Required)                                |
| [Click to Inspect: Original PDF | Extracted Text | Structured JSON | Confidence | Warnings]                                  |
| ----------------------------------------------------------------------------------------------------------------------------- |
| 🎴 Document 2: Discharge_Summary_Jane_Doe.pdf (1.1 MB)                                                                        |
| Status: [ 6. AI Review ] • Confidence: 98.6% • Errors: 0 • Warnings: 0                                                        |
| [Click to Inspect: Original PDF | Extracted Text | Structured JSON | Confidence | Warnings]                                  |
+-------------------------------------------------------------------------------------------------------------------------------+
| DOCUMENT INSPECTION DRAWER (When Document Clicked):                                                                           |
| [ 📄 Original PDF Preview ] | [ 📝 Extracted Text ] | [ 🌳 Structured JSON ] | [ 🎯 Confidence: 99.2% ] | [ ⚠️ Warnings: 1 ]  |
+-------------------------------------------------------------------------------------------------------------------------------+
```

---

## 🔄 7-Stage Live Ingestion Pipeline

1. **`1. Queued`**: File placed in processing queue.
2. **`2. Uploading`**: Secure binary upload to document storage.
3. **`3. OCR`**: High-resolution OCR matrix extraction.
4. **`4. Extracting`**: Clinical entity & patient MRN extraction.
5. **`5. Structuring`**: Schema transformation into 837 claim data elements.
6. **`6. AI Review`**: Pre-submission scrubber rule evaluation.
7. **`7. Completed`**: Document processed with 99.2% confidence rating.

---

## 🔍 Interactive Document Inspection Drawer

Clicking any document card in the queue opens the **Document Inspection Drawer**, allowing hospital staff to toggle between:

- **`📄 Original PDF`**: Interactive preview of original scanned PDF chart.
- **`📝 Extracted Text`**: Clean text output extracted from OCR.
- **`🌳 Structured JSON`**: Formatted JSON schema representation.
- **`🎯 Confidence`**: Overall accuracy rating (`99.2% Confidence`).
- **`⚠️ Errors & Warnings`**: Detailed listing of validation errors (`0 Errors`) and scrubber warnings (`1 Warning: Modifier -25 Required`).

---

## 🌐 Live Access

Access the Live Document Processing Center live:
- Open [http://localhost:8080/hospital-workspace.html#upload-documents](http://localhost:8080/hospital-workspace.html#upload-documents)
