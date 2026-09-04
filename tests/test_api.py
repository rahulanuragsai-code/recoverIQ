"""
Integration tests for RecoverIQ FastAPI endpoints.
Verifies seed, transaction listing, single analysis, batch simulation, metrics, and audit log.
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import Base, engine


@pytest.fixture(scope="module")
def client():
    # Ensure fresh DB tables
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as test_client:
        yield test_client


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_seed_transactions(client):
    response = client.post("/api/transactions/seed")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["count"] == 600
    assert data["seed"] == 42


def test_list_transactions(client):
    response = client.get("/api/transactions?page=1&page_size=20")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 600
    assert len(data["transactions"]) == 20
    first = data["transactions"][0]
    assert "transaction_id" in first
    assert "amount" in first
    assert first["is_synthetic"] is True


def test_analyze_single_transaction(client):
    # Analyze Edge Case 1 (Fraud camouflage)
    response = client.post("/api/transactions/tx_edge_fraud_001/analyze")
    assert response.status_code == 200
    data = response.json()
    assert data["policy_gate_verdict"] == "OVERRIDDEN"
    assert data["final_action"] == "escalate_human"
    assert data["recoverability_score"] == 0.0


def test_batch_simulation(client):
    response = client.post("/api/simulate/batch")
    assert response.status_code == 200
    data = response.json()
    assert data["total_transactions"] == 600
    assert data["seed"] == 42
    assert data["amount_at_risk"] > 0
    assert data["amount_recovered_ai"] > data["amount_recovered_baseline"]
    assert data["recovery_rate_uplift_pct"] > 0
    assert data["false_retries_avoided"] > 0
    assert data["policy_overrides_count"] > 0


def test_get_metrics(client):
    response = client.get("/api/metrics")
    assert response.status_code == 200
    data = response.json()
    assert data["total_transactions"] == 600
    assert data["amount_recovered_ai"] > 0
    assert "root_cause_breakdown" in data
    assert "action_breakdown" in data


def test_get_audit_log(client):
    response = client.get("/api/audit-log?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] > 0
    assert len(data["logs"]) <= 10
    first = data["logs"][0]
    assert "proposed_action" in first
    assert "final_action" in first
    assert "policy_verdict" in first
