import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_review_claim_contract():
    response = client.post("/api/review-claim", json={"claim_id": "CLM-2026-90124"})
    assert response.status_code == 200
    res = response.json()
    assert res["success"] is True
    data = res["data"]
    assert data["claim_id"] == "CLM-2026-90124"
    assert data["status"] == "REVIEWED"
    assert "findings" in data
    assert len(data["findings"]) > 0
    assert "recommended_fixes" in data

def test_run_ai_contract():
    response = client.post("/api/run-ai", json={"claim_id": "CLM-2026-90124"})
    assert response.status_code == 200
    res = response.json()
    assert res["success"] is True
    data = res["data"]
    assert data["status"] == "PASSED_AI_SCRUBBER"
    assert data["confidence_score"] > 0
    assert "structured_data" in data

def test_appeal_contract():
    response = client.post("/api/appeal", json={"claim_id": "CLM-77019"})
    assert response.status_code == 200
    res = response.json()
    assert res["success"] is True
    data = res["data"]
    assert data["case_id"] == "APP-2026-04"
    assert "appeal_letter" in data
    assert "evidence_checklist" in data

def test_claim_risk_contract():
    response = client.get("/api/claim-risk?claim_id=CLM-2026-90124")
    assert response.status_code == 200
    res = response.json()
    assert res["success"] is True
    data = res["data"]
    assert data["claim_id"] == "CLM-2026-90124"
    assert "revenue_at_risk" in data
    assert "denial_probability" in data

def test_validation_contract():
    response = client.get("/api/validation?claim_id=CLM-2026-90124")
    assert response.status_code == 200
    res = response.json()
    assert res["success"] is True
    data = res["data"]
    assert data["is_valid"] is True
    assert "warnings" in data
