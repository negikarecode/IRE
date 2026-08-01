import pytest
import time
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import create_access_token, create_refresh_token, decode_token

client = TestClient(app)

def test_jwt_token_creation_and_decoding():
    payload = {"sub": "usr_test123", "email": "test@hospital.org", "hospital_id": "hosp_123", "roles": ["Hospital Admin"]}
    access_token = create_access_token(payload)
    assert isinstance(access_token, str)
    
    decoded = decode_token(access_token)
    assert decoded["sub"] == "usr_test123"
    assert decoded["email"] == "test@hospital.org"
    assert decoded["type"] == "access"

def test_refresh_token_creation_and_decoding():
    payload = {"sub": "usr_test123", "email": "test@hospital.org"}
    refresh_token = create_refresh_token(payload)
    assert isinstance(refresh_token, str)
    
    decoded = decode_token(refresh_token)
    assert decoded["sub"] == "usr_test123"
    assert decoded["type"] == "refresh"

def test_auth_me_endpoint_unauthorized():
    with TestClient(app) as test_c:
        res = test_c.get("/api/v1/auth/me")
        assert res.status_code == 401
        res_json = res.json()
        assert res_json["success"] is False
        assert res_json["error"]["code"] == "UNAUTHORIZED"

def test_auth_register_validation_error():
    with TestClient(app) as test_c:
        # Invalid email format
        invalid_payload = {
            "hospital_name": "Test Hospital",
            "facility_type": "Inpatient Hospital",
            "email": "invalid-email-format",
            "password": "Password123!",
            "confirm_password": "Password123!",
            "admin_full_name": "Dr. Test"
        }
        res = test_c.post("/api/v1/auth/hospitals/register", json=invalid_payload)
        assert res.status_code == 422
        res_json = res.json()
        assert res_json["success"] is False
