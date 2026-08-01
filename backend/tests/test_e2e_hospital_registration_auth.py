import pytest
import time
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_full_e2e_hospital_registration_and_login_flow():
    with TestClient(app) as client:
        unique_email = f"cfo_{int(time.time())}@metrohealthsystem.org"
        hospital_name = f"Metro Health System {int(time.time())}"
        password = "SuperSecurePassword123!"

        # 1. POST /api/v1/auth/hospitals/register
        reg_payload = {
            "hospital_name": hospital_name,
            "facility_type": "Inpatient Hospital",
            "npi_number": "1982736450",
            "email": unique_email,
            "password": password,
            "confirm_password": password,
            "admin_full_name": "Dr. Sarah Jenkins"
        }

        reg_response = client.post("/api/v1/auth/hospitals/register", json=reg_payload)
        assert reg_response.status_code == 201, f"Registration failed: {reg_response.text}"

        reg_data = reg_response.json()
        assert reg_data["success"] is True
        data = reg_data["data"]
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["hospital_name"] == hospital_name
        assert "Hospital Admin" in data["roles"]

        access_token = data["access_token"]

        # 2. GET /api/v1/auth/me (Verify JWT Token Authentication)
        me_response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert me_response.status_code == 200, f"Session verification failed: {me_response.text}"
        me_res = me_response.json()
        assert me_res["success"] is True
        me_data = me_res["data"]
        assert me_data["email"] == unique_email
        assert me_data["hospital_name"] == hospital_name
        assert me_data["is_active"] is True

        # 3. Duplicate Email Registration (Verify Structured Backend Error)
        dup_response = client.post("/api/v1/auth/hospitals/register", json=reg_payload)
        assert dup_response.status_code == 409
        dup_data = dup_response.json()
        assert dup_data["success"] is False
        assert "already registered" in dup_data["message"].lower()

        # 4. POST /api/v1/auth/hospitals/login (Verify Login Flow)
        login_payload = {
            "email": unique_email,
            "password": password,
            "remember_me": True
        }
        login_response = client.post("/api/v1/auth/hospitals/login", json=login_payload)
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"

        login_res = login_response.json()
        assert login_res["success"] is True
        login_data = login_res["data"]
        assert "access_token" in login_data
        assert login_data["hospital_name"] == hospital_name

        # 5. Invalid Password Login Attempt
        bad_login_payload = {
            "email": unique_email,
            "password": "WrongPassword123!"
        }
        bad_login_response = client.post("/api/v1/auth/hospitals/login", json=bad_login_payload)
        assert bad_login_response.status_code == 401
        bad_res = bad_login_response.json()
        assert bad_res["success"] is False
