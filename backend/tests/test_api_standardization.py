import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_success_response_structure():
    """Test that health check endpoint returns exact standardized success response schema."""
    response = client.get("/api/v1/healthz")
    assert response.status_code == 200
    json_data = response.json()
    
    assert "success" in json_data
    assert json_data["success"] is True
    assert "message" in json_data
    assert isinstance(json_data["message"], str)
    assert "data" in json_data
    assert isinstance(json_data["data"], dict)

def test_validation_failure_response_structure():
    """Test that invalid request body returns standardized error response schema with 422 status."""
    # POST to /api/v1/auth/login without required fields
    response = client.post("/api/v1/auth/login", json={})
    assert response.status_code == 422
    json_data = response.json()
    
    assert "success" in json_data
    assert json_data["success"] is False
    assert "message" in json_data
    assert "error" in json_data
    assert "code" in json_data["error"]
    assert json_data["error"]["code"] == "VALIDATION_ERROR"
    assert "details" in json_data["error"]
    assert isinstance(json_data["error"]["details"], dict)

def test_unauthorized_failure_response_structure():
    """Test that unauthorized request returns standardized error response schema with 401 status."""
    response = client.get("/api/v1/users/me")
    assert response.status_code == 401
    json_data = response.json()
    
    assert json_data["success"] is False
    assert "message" in json_data
    assert "error" in json_data
    assert json_data["error"]["code"] == "UNAUTHORIZED"
    assert "details" in json_data["error"]

def test_not_found_failure_response_structure():
    """Test that accessing non-existent API resource returns standardized 404 error response."""
    response = client.get("/api/v1/non_existent_resource")
    assert response.status_code == 404
    json_data = response.json()
    
    assert json_data["success"] is False
    assert "message" in json_data
    assert "error" in json_data
    assert json_data["error"]["code"] == "NOT_FOUND"
    assert "details" in json_data["error"]
