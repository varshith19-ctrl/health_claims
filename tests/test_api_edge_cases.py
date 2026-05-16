"""
Test Suite 4 — API & Edge Cases Validation.
Tests the FastAPI endpoints for valid requests, validation errors,
business rule overrides, and schema compliance.
"""
import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


# ── Health Endpoint Tests ───────────────────────────────────────────

class TestHealthEndpoint:
    """Verify the health check endpoint works."""

    def test_health_returns_200(self):
        response = client.get("/api/health")
        assert response.status_code == 200

    def test_health_returns_healthy_status(self):
        response = client.get("/api/health")
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data


# ── Valid Claim Submission Tests ────────────────────────────────────

class TestValidClaimSubmission:
    """Verify a valid claim returns a complete, correct response."""

    VALID_CLAIM = {
        "claim_id": "TEST001",
        "patient_id": "P001",
        "provider_id": "PR100",
        "diagnosis_code": "D10",
        "procedure_code": "PROC1",
        "billed_amount": 15000.0,
    }

    def test_valid_claim_returns_200(self):
        response = client.post("/api/predict-claim", json=self.VALID_CLAIM)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

    def test_response_has_all_required_fields(self):
        response = client.post("/api/predict-claim", json=self.VALID_CLAIM)
        data = response.json()
        required_fields = [
            "claim_id", "risk", "risk_score", "score", "prediction",
            "reasons", "feature_contributions", "top_2_features",
            "policy_explanation", "recommendations", "execution_flow",
        ]
        for field in required_fields:
            assert field in data, f"Missing field in response: {field}"

    def test_response_json_is_valid(self):
        response = client.post("/api/predict-claim", json=self.VALID_CLAIM)
        data = response.json()
        assert isinstance(data["reasons"], list), "Reasons should be a list"
        assert isinstance(data["recommendations"], list), "Recommendations should be a list"
        assert isinstance(data["feature_contributions"], dict), "Contributions should be a dict"
        assert isinstance(data["score"], float), "Score should be a float"

    def test_prediction_label_is_valid(self):
        response = client.post("/api/predict-claim", json=self.VALID_CLAIM)
        data = response.json()
        assert data["prediction"] in ("ACCEPTED", "DENIED", "MEDIUM"), \
            f"Invalid prediction label: {data['prediction']}"


# ── Validation Error Tests (Edge Cases) ─────────────────────────────

class TestValidationErrors:
    """Verify the API correctly rejects invalid input."""

    def test_missing_claim_id_returns_422(self):
        bad_claim = {
            "patient_id": "P001",
            "provider_id": "PR100",
            "diagnosis_code": "D10",
            "procedure_code": "PROC1",
            "billed_amount": 15000.0,
        }
        response = client.post("/api/predict-claim", json=bad_claim)
        assert response.status_code == 422, "Should return 422 for missing claim_id"

    def test_missing_provider_id_returns_422(self):
        bad_claim = {
            "claim_id": "TEST002",
            "diagnosis_code": "D10",
            "procedure_code": "PROC1",
            "billed_amount": 15000.0,
        }
        response = client.post("/api/predict-claim", json=bad_claim)
        assert response.status_code == 422, "Should return 422 for missing provider_id"

    def test_negative_billed_amount_returns_422(self):
        bad_claim = {
            "claim_id": "TEST003",
            "provider_id": "PR100",
            "diagnosis_code": "D10",
            "procedure_code": "PROC1",
            "billed_amount": -500.0,
        }
        response = client.post("/api/predict-claim", json=bad_claim)
        assert response.status_code == 422, "Should return 422 for negative billed_amount"

    def test_zero_billed_amount_returns_422(self):
        bad_claim = {
            "claim_id": "TEST004",
            "provider_id": "PR100",
            "diagnosis_code": "D10",
            "procedure_code": "PROC1",
            "billed_amount": 0.0,
        }
        response = client.post("/api/predict-claim", json=bad_claim)
        assert response.status_code == 422, "Should return 422 for zero billed_amount"

    def test_empty_body_returns_422(self):
        response = client.post("/api/predict-claim", json={})
        assert response.status_code == 422, "Should return 422 for empty body"


# ── Business Rule Override Tests ────────────────────────────────────

class TestBusinessRules:
    """Verify hard-coded business rules override ML predictions."""

    def test_extreme_billed_amount_forces_high_risk(self):
        """If billed amount is >5x the regional average, force HIGH risk."""
        extreme_claim = {
            "claim_id": "TEST_EXTREME",
            "patient_id": "P001",
            "provider_id": "PR100",
            "diagnosis_code": "D10",
            "procedure_code": "PROC1",
            "billed_amount": 999999.0,  # Extremely high amount
        }
        response = client.post("/api/predict-claim", json=extreme_claim)
        assert response.status_code == 200
        data = response.json()
        assert data["risk"] == "HIGH", f"Extreme billed amount should force HIGH risk, got {data['risk']}"
        assert data["prediction"] == "DENIED", f"Extreme amount should be DENIED, got {data['prediction']}"

    def test_low_amount_accepted(self):
        """A claim with a very low, normal billed amount should trend toward ACCEPTED."""
        low_claim = {
            "claim_id": "TEST_LOW",
            "patient_id": "P001",
            "provider_id": "PR100",
            "diagnosis_code": "D10",
            "procedure_code": "PROC1",
            "billed_amount": 100.0,  # Very low, normal amount
        }
        response = client.post("/api/predict-claim", json=low_claim)
        assert response.status_code == 200
        data = response.json()
        # A very low amount should have a low denial probability
        assert data["score"] < 0.7, f"Low billed amount should have low risk score, got {data['score']}"
