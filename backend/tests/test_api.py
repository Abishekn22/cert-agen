"""Integration tests for FastAPI endpoints."""
from datetime import date, timedelta
from unittest.mock import AsyncMock, patch
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.main import app
from app.database import Base, get_db
from app.models.certificate import Certificate

# Setup shared in-memory test DB using StaticPool
test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()
    today = date.today()

    cert1 = Certificate(
        certificate_id="ABC123",
        customer_name="Customer A",
        domain="api.customera.com",
        certificate_type="TLS",
        issued_at=today - timedelta(days=100),
        expires_at=today + timedelta(days=12),
        status="ACTIVE",
        revoked=False,
    )
    cert2 = Certificate(
        certificate_id="XYZ789",
        customer_name="Customer B",
        domain="legacy.customerb.org",
        certificate_type="TLS",
        issued_at=today - timedelta(days=200),
        expires_at=today + timedelta(days=50),
        status="REVOKED",
        revoked=True,
        revocation_date=today - timedelta(days=10),
        revocation_reason="KeyCompromise",
    )
    db.add_all([cert1, cert2])
    db.commit()
    db.close()
    yield
    Base.metadata.drop_all(bind=test_engine)

client = TestClient(app)

def test_health_endpoint():
    with patch("app.agent.ollama_client.OllamaClient.check_health", new_callable=AsyncMock) as mock_health:
        mock_health.return_value = {"available": True, "status": "connected", "model_ready": True}
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["database"] == "available"
        assert data["ollama"] == "available"

def test_get_certificate_api():
    res = client.get("/api/certificates/ABC123")
    assert res.status_code == 200
    data = res.json()
    assert data["certificate_id"] == "ABC123"
    assert data["customer_name"] == "Customer A"

    # Non-existent
    res_404 = client.get("/api/certificates/NOTFOUND")
    assert res_404.status_code == 404

def test_get_expiring_certificates_api():
    res = client.get("/api/certificates/expiring?days=30")
    assert res.status_code == 200
    items = res.json()
    assert len(items) == 1
    assert items[0]["certificate_id"] == "ABC123"

def test_create_renewal_api():
    res = client.post("/api/renewals", json={"certificate_id": "ABC123", "requested_by": "api-test"})
    assert res.status_code == 201
    data = res.json()
    assert data["certificate_id"] == "ABC123"
    assert data["request_id"].startswith("REN-")

    # Duplicate should fail with 409
    res_dup = client.post("/api/renewals", json={"certificate_id": "ABC123"})
    assert res_dup.status_code == 409

    # Revoked should fail with 409
    res_rev = client.post("/api/renewals", json={"certificate_id": "XYZ789"})
    assert res_rev.status_code == 409

@pytest.mark.asyncio
async def test_agent_api_with_mocked_ollama():
    mock_tool_call_response = {
        "message": {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "id": "call_123",
                    "function": {
                        "name": "get_expiring_certificates",
                        "arguments": {"days": 30},
                    }
                }
            ]
        }
    }
    mock_synthesis_response = {
        "message": {
            "role": "assistant",
            "content": "1 certificate expires within the next 30 days: ABC123.",
        }
    }

    with patch("app.agent.ollama_client.OllamaClient.chat", new_callable=AsyncMock) as mock_chat:
        mock_chat.side_effect = [mock_tool_call_response, mock_synthesis_response]

        response = client.post("/api/agent", json={"question": "Show all certificates expiring in the next 30 days"})
        assert response.status_code == 200
        data = response.json()
        assert "ABC123" in data["answer"]
        assert len(data["tool_calls"]) == 1
        assert data["tool_calls"][0]["tool_name"] == "get_expiring_certificates"
        assert data["tool_calls"][0]["success"] is True
        assert data["execution_time_ms"] >= 0
