# ChatGPT-Style Document Upload & Ingestion Pipeline Manual

This document details the redesigned **Document Ingestion & OCR Processing Center**, styled after the **ChatGPT file upload experience**.

---

## 🎨 Design Concept: ChatGPT File Processing Experience

Rather than a static file upload form, the document ingestion engine features a dynamic, real-time animated processing pipeline:

```
+---------------------------------------------------------------------------------------------------------------+
| 📤 Document Ingestion & OCR Processing Center (ChatGPT File Processing UX)                                   |
+---------------------------------------------------------------------------------------------------------------+
|                                                                                                               |
| +-----------------------------------------------------------------------------------------------------------+ |
| |  ☁️ DRAG AND DROP CLINICAL DOCUMENTS HERE OR CLICK TO BROWSE                                               | |
| |  Supports PDF, TIFF, PNG, JPEG, EDI 837/835 • Auto-detects Operative Notes, Superbills, EOBs             | |
| +-----------------------------------------------------------------------------------------------------------+ |
|                                                                                                               |
| 📂 ACTIVE UPLOAD & EXTRACTION PIPELINE:                                                                       |
| +-----------------------------------------------------------------------------------------------------------+ |
| | 📄 Operative_Note_Surgical_Receipt_0728.pdf (2.4 MB)                                 [ 85% Processing... ]| |
| | Progress: [========================================================================.......] (85%)       | |
| | Status: ⏳ Finding Diagnosis... (ICD-10 K80.20 matched)                                                   | |
| |                                                                                                           | |
| | WORKFLOW STEPPERS:                                                                                        | |
| | [✓ Uploaded] ➔ [✓ OCR Engine] ➔ [✓ Extract Data] ➔ [⚡ AI Parsing] ➔ [⏳ Validation] ➔ [Ready for Review] |
| +-----------------------------------------------------------------------------------------------------------+ |
|                                                                                                               |
| 🌳 REAL-TIME STRUCTURED DATA PREVIEW (Once Extracted):                                                       |
| - Patient Name: Jane Doe \| MRN: MRN-90214                                                                   |
| - Detected Document Type: Operative Surgical Report & Itemized Bill                                           |
| - Extracted CPT Codes: CPT 47562 ($12,450.00), CPT 99214 ($450.00)                                           |
| - Extracted ICD-10 Diagnoses: K80.20 (Gallbladder Calculus), R07.9 (Chest Pain)                               |
| - Table Grids Parsed: 2 Grids (100% Cell Accuracy)                                                            |
|                                                                                                               |
| [ 🚀 Proceed to AI Claim Review Workspace ]                                                                   |
+---------------------------------------------------------------------------------------------------------------+
```

---

## 🔄 8-Step Progress Pipeline & Animated Messages

1. **`1. Drag PDF`**: File drop & format detection.
2. **`2. Upload Progress`**: Real-time progress bar fill animation (`Reading PDF...`).
3. **`3. OCR Processing`**: Text, handwriting, and layout analysis (`Detecting Tables...`).
4. **`4. AI Extraction`**: Clinical entity extraction (`Extracting Patient...`).
5. **`5. Structured Data Preview`**: Billed line item extraction (`Reading Bill...`).
6. **`6. Detected Documents`**: Diagnosis code identification (`Finding Diagnosis...`).
7. **`7. Validation`**: Pre-submission rule validation.
8. **`8. Ready for Review`**: Done state with **"Proceed to AI Claim Review Workspace"** button.

---

## 🌐 Live Access

Access the upload experience live:
- Open [http://localhost:8080/hospital-workspace.html#upload-documents](http://localhost:8080/hospital-workspace.html#upload-documents)
