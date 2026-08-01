# Enterprise Healthcare Platform - Complete REST API Documentation

**Version**: 1.0.0  
**Specification**: OpenAPI 3.0 / Standardized JSON Contract  
**Base URL**: `/api/v1`  
**Interactive Docs**: `/api/v1/docs` (Swagger UI) / `/api/v1/redoc` (ReDoc)  
**OpenAPI JSON Export**: [`api/openapi/openapi.json`](file:///home/aryan/Videos/IRE/api/openapi/openapi.json) & [`docs/openapi.json`](file:///home/aryan/Videos/IRE/docs/openapi.json)

---

## Standardized API Response Contracts

All REST API endpoints implement a strict, predictable JSON response envelope:

### 1. Success Contract (HTTP 200 OK / 201 Created / 202 Accepted)
```json
{
    "success": true,
    "message": "Human-readable operational message",
    "data": {}
}
```

### 2. Error Contract (HTTP 400, 401, 403, 404, 409, 422, 500)
```json
{
    "success": false,
    "message": "Human-readable error description",
    "error": {
        "code": "ERROR_CODE",
        "details": {}
    }
}
```

---

## 1. Authentication & Security Endpoints (`/auth`)

### 1.1 Register Hospital & Admin
- **Purpose**: Registers a new SaaS hospital tenant account and creates the initial Hospital Administrator user.
- **Method**: `POST`
- **Path**: `/api/v1/auth/hospitals/register`
- **Authentication**: None (Public Endpoint)
- **Validation Rules**:
  - `email`: Valid EmailStr format.
  - `password`: String (min length: 8, max length: 128).
  - `confirm_password`: Must match `password`.
  - `facility_type`: Must be one of `Inpatient Hospital`, `Outpatient Clinic`, `Diagnostic Center`.
- **Request Example**:
  ```bash
  curl -X POST "http://localhost:8000/api/v1/auth/hospitals/register" \
    -H "Content-Type: application/json" \
    -d '{
      "hospital_name": "Metro General Hospital",
      "facility_type": "Inpatient Hospital",
      "npi_number": "1982736450",
      "email": "admin@metrohospital.org",
      "password": "SuperSecurePassword123!",
      "confirm_password": "SuperSecurePassword123!",
      "admin_full_name": "Dr. Sarah Jenkins"
    }'
  ```
- **Response Example (201 Created)**:
  ```json
  {
      "success": true,
      "message": "Hospital account and administrator created successfully",
      "data": {
          "hospital_id": "hosp_9a8b7c6d",
          "hospital_name": "Metro General Hospital",
          "user_id": "usr_1a2b3c4d",
          "email": "admin@metrohospital.org",
          "roles": ["Hospital Admin"],
          "access_token": "eyJhbGciOiJIUzI1Ni...",
          "refresh_token": "eyJhbGciOiJIUzI1Ni...",
          "token_type": "bearer"
      }
  }
  ```

---

### 1.2 Hospital Staff Login
- **Purpose**: Authenticates hospital staff credentials and issues access & refresh tokens.
- **Method**: `POST`
- **Path**: `/api/v1/auth/hospitals/login`
- **Authentication**: None
- **Validation Rules**: Valid `email` format and non-empty `password`.
- **Request Example**:
  ```bash
  curl -X POST "http://localhost:8000/api/v1/auth/hospitals/login" \
    -H "Content-Type: application/json" \
    -d '{
      "email": "admin@metrohospital.org",
      "password": "SuperSecurePassword123!",
      "remember_me": true
    }'
  ```
- **Response Example (200 OK)**:
  ```json
  {
      "success": true,
      "message": "Login successful",
      "data": {
          "access_token": "eyJhbGciOiJIUzI1Ni...",
          "refresh_token": "eyJhbGciOiJIUzI1Ni...",
          "token_type": "bearer",
          "expires_in": 86400,
          "user_id": "usr_1a2b3c4d",
          "hospital_id": "hosp_9a8b7c6d",
          "hospital_name": "Metro General Hospital",
          "roles": ["Hospital Admin"]
      }
  }
  ```

---

### 1.3 Refresh Access Token
- **Purpose**: Exchanging active Refresh Token for a new Access/Refresh token pair with automatic session rotation and DB revocation.
- **Method**: `POST`
- **Path**: `/api/v1/auth/refresh`
- **Authentication**: Valid Refresh Token in body.
- **Validation Rules**: `refresh_token` string required. Must exist in database `SessionModel`.
- **Request Example**:
  ```bash
  curl -X POST "http://localhost:8000/api/v1/auth/refresh" \
    -H "Content-Type: application/json" \
    -d '{
      "refresh_token": "eyJhbGciOiJIUzI1Ni..."
    }'
  ```
- **Response Example (200 OK)**:
  ```json
  {
      "success": true,
      "message": "Tokens refreshed successfully",
      "data": {
          "access_token": "eyJhbGciOiJIUzI1Ni...",
          "refresh_token": "eyJhbGciOiJIUzI1Ni...",
          "expires_in": 86400,
          "user_id": "usr_1a2b3c4d",
          "hospital_id": "hosp_9a8b7c6d"
      }
  }
  ```

---

## 2. Document & Ingestion Endpoints (`/documents`, `/v1_docs`)

### 2.1 Secure Document Upload
- **Purpose**: Uploads medical documents (PDFs, Images, Word) with 64KB streaming buffers, checksum calculation, MIME/extension verification, and virus scanning.
- **Method**: `POST`
- **Path**: `/api/v1/documents/upload`
- **Authentication**: OAuth2 Bearer JWT (`Authorization: Bearer <token>`)
- **Headers**: `X-Tenant-ID` (Optional), `X-Hospital-ID` (Optional)
- **Form Parameters**:
  - `file`: UploadFile (Allowed: `.pdf`, `.jpg`, `.jpeg`, `.png`, `.tiff`, `.tif`, Max: 50 MB)
  - `claim_id`: String (Optional)
- **Request Example**:
  ```bash
  curl -X POST "http://localhost:8000/api/v1/documents/upload" \
    -H "Authorization: Bearer <access_token>" \
    -F "file=@/path/to/discharge_summary.pdf" \
    -F "claim_id=clm_90214"
  ```
- **Response Example (201 Created)**:
  ```json
  {
      "success": true,
      "message": "Document uploaded successfully",
      "data": {
          "id": "doc_8f9a0b1c",
          "hospital_id": "hosp_9a8b7c6d",
          "claim_id": "clm_90214",
          "original_filename": "discharge_summary.pdf",
          "mime_type": "application/pdf",
          "file_size_bytes": 1048576,
          "checksum": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
          "processing_status": "pending",
          "virus_scan_status": "clean",
          "created_at": "2026-08-01T20:15:00.000Z"
      }
  }
  ```

---

## 3. Modular OCR Service (`/ocr`)

### 3.1 Synchronous OCR Text Extraction
- **Purpose**: Extracts text, layout regions, bounding boxes, tables, and confidence scores from medical documents.
- **Method**: `POST`
- **Path**: `/api/v1/ocr/extract`
- **Authentication**: OAuth2 Bearer JWT
- **Form Parameters**: `file`: UploadFile (PDF / Image)
- **Request Example**:
  ```bash
  curl -X POST "http://localhost:8000/api/v1/ocr/extract" \
    -H "Authorization: Bearer <access_token>" \
    -F "file=@/path/to/lab_report.png"
  ```
- **Response Example (200 OK)**:
  ```json
  {
      "success": true,
      "message": "OCR extraction completed successfully",
      "data": {
          "filename": "lab_report.png",
          "page_count": 1,
          "ocr_confidence": 0.965,
          "text": "PATIENT: Jane Doe\nDIAGNOSIS: Acute Appendicitis...",
          "tables": [
              {
                  "headers": ["Test", "Result", "Unit", "Reference"],
                  "rows": [["WBC", "14.5", "10^3/uL", "4.5-11.0"]]
              }
          ]
      }
  }
  ```

---

## 4. AI Reasoning & Processing Endpoints

### 4.1 Claim Validation (`/validation`)
- **Purpose**: Audits medical claim documentation against ICD/CPT coding rules, medical necessity, and required attachment criteria.
- **Method**: `POST`
- **Path**: `/api/v1/validation/{claim_id}`
- **Authentication**: OAuth2 Bearer JWT
- **Path Parameters**: `claim_id`: String
- **Response Example (200 OK)**:
  ```json
  {
      "success": true,
      "message": "Claim validation completed successfully",
      "data": {
          "claim_id": "clm_90214",
          "overall_status": "review_required",
          "total_findings": 2,
          "critical_findings": 1,
          "high_findings": 1,
          "findings": [
              {
                  "id": "val_1",
                  "category": "missing_authorization",
                  "severity": "critical",
                  "explanation": "Pre-authorization letter missing for laparoscopic appendectomy procedure."
              }
          ]
      }
  }
  ```

---

### 4.2 Medical Coding Review (`/coding-review`)
- **Purpose**: Detects ICD-10 and CPT coding mismatches, missing modifiers, and unbundling issues.
- **Method**: `POST`
- **Path**: `/api/v1/coding-review/{claim_id}`
- **Authentication**: OAuth2 Bearer JWT

---

### 4.3 Denial Prediction (`/denial-prediction`)
- **Purpose**: Predicts probability of claim denial (0.0 to 1.0) and lists key risk factors.
- **Method**: `POST`
- **Path**: `/api/v1/denial-prediction/{claim_id}`
- **Authentication**: OAuth2 Bearer JWT

---

### 4.4 Revenue Leakage Detection (`/revenue-leakage`)
- **Purpose**: Identifies unbilled procedures, missed implants, and underbilled charges.
- **Method**: `POST`
- **Path**: `/api/v1/revenue-leakage/{claim_id}`
- **Authentication**: OAuth2 Bearer JWT

---

### 4.5 Corrected Claim Preview (`/corrected-claim`)
- **Purpose**: Generates side-by-side claim diffs with AI recommendations ready for reviewer approval.
- **Method**: `POST`
- **Path**: `/api/v1/corrected-claim/{claim_id}`
- **Authentication**: OAuth2 Bearer JWT

---

## 5. Document Claim Assembly & Appeals (`/document-claims`)

### 5.1 List Document Claims
- **Purpose**: Retrieves all assembled document claims for the authenticated hospital tenant.
- **Method**: `GET`
- **Path**: `/api/v1/document-claims/`
- **Authentication**: OAuth2 Bearer JWT

---

## 6. System Settings & Configuration (`/settings`)

### 6.1 Get Settings
- **Purpose**: Fetches system and hospital configuration settings.
- **Method**: `GET`
- **Path**: `/api/v1/settings/`
- **Authentication**: OAuth2 Bearer JWT
