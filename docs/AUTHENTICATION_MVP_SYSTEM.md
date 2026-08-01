# Production Authentication & MVP Architecture Manual

This document details the **Production-Ready PostgreSQL & SQLAlchemy Authentication System** and the **MVP-First Architecture Decoupling**.

---

## 🏛️ MVP Decoupling & Isolation

1. **Decoupled Platform Console**:
   - Internal Platform Console references and switcher buttons have been completely removed from the Hospital Workspace UI.
   - Every user operates strictly as a hospital employee in their isolated hospital workspace (`hospital-workspace.html#dashboard`).
2. **SaaS Landing Page (`index.html`)**:
   - Production SaaS landing page with features, pricing, hospital registration modal, and sign-in modal.

---

## 🔐 Database Models & Schema (`auth_models.py`)

- **`auth_hospitals`**: `id`, `name`, `facility_type`, `npi_number`, `created_at`
- **`auth_organizations`**: `id`, `hospital_id`, `name`, `created_at`
- **`auth_roles`**: `id`, `hospital_id`, `name`, `description`
  - Default Roles Created per Hospital:
    1. **`Hospital Admin`**
    2. **`Billing Executive`**
    3. **`Reviewer`**
- **`auth_users`**: `id`, `hospital_id`, `organization_id`, `email`, `hashed_password` (Bcrypt), `full_name`, `is_active`
- **`auth_sessions`**: `id`, `user_id`, `token`, `refresh_token`, `expires_at`

---

## 🔌 Authentication Endpoints

1. **`POST /api/v1/auth/hospitals/register`** (or `POST /api/v1/auth/register`):
   - Registers Hospital, Organization, 3 Default Hospital Roles, and Admin User in Database.
   - Issues JWT Access Token & Refresh Token.
2. **`POST /api/v1/auth/hospitals/login`** (or `POST /api/v1/auth/login`):
   - Authenticates against database using Bcrypt verification.
   - Supports `Remember Me` extended session duration.
3. **`GET /api/v1/auth/me`**:
   - Session validation and profile retrieval endpoint.
4. **`POST /api/v1/auth/refresh`**:
   - Refresh token rotation.
5. **`POST /api/v1/auth/logout`**:
   - Session revocation.

---

## 🌐 Live Access

- **SaaS Landing Page & Auth**: [http://localhost:8080/index.html](http://localhost:8080/index.html)
- **Hospital Workspace**: [http://localhost:8080/hospital-workspace.html](http://localhost:8080/hospital-workspace.html)
- **FastAPI OpenAPI Swagger**: [http://localhost:8000/docs#/Authentication%20%26%20JWT](http://localhost:8000/docs#/Authentication%20%26%20JWT)
