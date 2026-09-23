"""Unit tests for Renewal Service and tools."""
from datetime import date, timedelta
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models.certificate import Certificate
from app.models.renewal import RenewalRequest
from app.services.renewal_service import RenewalService, RenewalValidationError
from app.tools.renewal_tools import create_renewal_request_tool

@pytest.fixture
def db_session():
    """Create in-memory SQLite database for testing renewals."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()

    today = date.today()

    # Seed test certs
    cert_valid = Certificate(
        certificate_id="ABC123",
        customer_name="Customer A",
        domain="api.customera.com",
        certificate_type="TLS",
        issued_at=today - timedelta(days=100),
        expires_at=today + timedelta(days=20),
        status="ACTIVE",
        revoked=False,
    )
    cert_revoked = Certificate(
        certificate_id="XYZ789",
        customer_name="Customer B",
        domain="legacy.customerb.org",
        certificate_type="TLS",
        issued_at=today - timedelta(days=200),
        expires_at=today + timedelta(days=50),
        status="REVOKED",
        revoked=True,
        revocation_date=today - timedelta(days=5),
        revocation_reason="KeyCompromise",
    )
    db.add_all([cert_valid, cert_revoked])
    db.commit()

    try:
        yield db
    finally:
        db.close()

def test_create_valid_renewal(db_session):
    res = RenewalService.create_renewal(db_session, "ABC123", requested_by="tester")
    assert res["status"] == "PENDING"
    assert res["certificate_id"] == "ABC123"
    assert res["customer_name"] == "Customer A"
    assert res["request_id"].startswith("REN-")

    # Verify record in DB
    record = db_session.query(RenewalRequest).filter_by(request_id=res["request_id"]).first()
    assert record is not None
    assert record.requested_by == "tester"

def test_prevent_duplicate_renewal(db_session):
    # First renewal succeeds
    RenewalService.create_renewal(db_session, "ABC123")

    # Second renewal must raise RenewalValidationError with conflict status 409
    with pytest.raises(RenewalValidationError) as exc:
        RenewalService.create_renewal(db_session, "ABC123")
    assert "already exists" in str(exc.value)
    assert exc.value.status_code == 409

    # Tool output returns success=False
    tool_res = create_renewal_request_tool(db_session, "ABC123")
    assert tool_res["success"] is False
    assert "already exists" in tool_res["error"]

def test_reject_renewal_for_revoked_cert(db_session):
    with pytest.raises(RenewalValidationError) as exc:
        RenewalService.create_renewal(db_session, "XYZ789")
    assert "already revoked" in str(exc.value)
    assert exc.value.status_code == 409

    tool_res = create_renewal_request_tool(db_session, "XYZ789")
    assert tool_res["success"] is False
    assert "already revoked" in tool_res["error"]

def test_reject_renewal_for_missing_cert(db_session):
    with pytest.raises(RenewalValidationError) as exc:
        RenewalService.create_renewal(db_session, "NONEXISTENT999")
    assert "was not found" in str(exc.value)
    assert exc.value.status_code == 404

    tool_res = create_renewal_request_tool(db_session, "NONEXISTENT999")
    assert tool_res["success"] is False
    assert "was not found" in tool_res["error"]
