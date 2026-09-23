"""Unit tests for Certificate Service and tools."""
from datetime import date, timedelta
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models.certificate import Certificate
from app.services.certificate_service import CertificateService
from app.tools.certificate_tools import (
    get_certificate_tool,
    get_expiring_certificates_tool,
    check_revocation_tool,
    get_customer_certificates_tool,
)

@pytest.fixture
def db_session():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()

    today = date.today()

    # Seed test data
    cert_active = Certificate(
        certificate_id="ABC123",
        customer_name="Customer A",
        domain="api.customera.com",
        certificate_type="TLS",
        issued_at=today - timedelta(days=100),
        expires_at=today + timedelta(days=15),
        status="ACTIVE",
        revoked=False,
    )
    cert_revoked = Certificate(
        certificate_id="XYZ789",
        customer_name="Customer B",
        domain="legacy.customerb.org",
        certificate_type="TLS",
        issued_at=today - timedelta(days=200),
        expires_at=today + timedelta(days=165),
        status="REVOKED",
        revoked=True,
        revocation_date=today - timedelta(days=10),
        revocation_reason="KeyCompromise",
    )
    cert_far = Certificate(
        certificate_id="FAR001",
        customer_name="Customer A",
        domain="vault.customera.com",
        certificate_type="mTLS",
        issued_at=today - timedelta(days=50),
        expires_at=today + timedelta(days=120),
        status="ACTIVE",
        revoked=False,
    )

    db.add_all([cert_active, cert_revoked, cert_far])
    db.commit()

    try:
        yield db
    finally:
        db.close()

def test_get_existing_certificate(db_session):
    cert = CertificateService.get_by_id(db_session, "ABC123")
    assert cert is not None
    assert cert.certificate_id == "ABC123"
    assert cert.customer_name == "Customer A"
    assert cert.status == "ACTIVE"

def test_get_missing_certificate(db_session):
    cert = CertificateService.get_by_id(db_session, "NONEXISTENT999")
    assert cert is None

    tool_result = get_certificate_tool(db_session, "NONEXISTENT999")
    assert tool_result["found"] is False
    assert "was not found" in tool_result["message"]

def test_get_expiring_certificates(db_session):
    # Expiring within 30 days should find ABC123, but not FAR001 (120 days) or XYZ789 (revoked)
    expiring = CertificateService.get_expiring_certificates(db_session, days=30)
    assert len(expiring) == 1
    assert expiring[0]["certificate_id"] == "ABC123"
    assert expiring[0]["days_remaining"] == 15

    tool_result = get_expiring_certificates_tool(db_session, days=30)
    assert tool_result["count"] == 1
    assert tool_result["certificates"][0]["certificate_id"] == "ABC123"

def test_customer_certificates(db_session):
    certs = CertificateService.get_by_customer(db_session, "Customer A")
    assert len(certs) == 2
    cert_ids = [c["certificate_id"] for c in certs]
    assert "ABC123" in cert_ids
    assert "FAR001" in cert_ids

    tool_result = get_customer_certificates_tool(db_session, "Customer A")
    assert tool_result["count"] == 2

def test_revocation_checks(db_session):
    # Test revoked cert
    revoked_info = CertificateService.check_revocation(db_session, "XYZ789")
    assert revoked_info["revoked"] is True
    assert revoked_info["revocation_reason"] == "KeyCompromise"

    # Test non-revoked cert
    active_info = CertificateService.check_revocation(db_session, "ABC123")
    assert active_info["revoked"] is False
    assert active_info["revocation_date"] is None
