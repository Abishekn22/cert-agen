"""Deterministic certificate tool implementations called by the AI agent."""
from typing import Any, Dict, List
from datetime import date, datetime
from sqlalchemy.orm import Session
from app.services.certificate_service import CertificateService
from app.utils.logger import logger

def get_certificate_tool(db: Session, certificate_id: str) -> Dict[str, Any]:
    """Retrieve complete information about a certificate by its ID."""
    logger.info(f"Executing tool get_certificate for ID: {certificate_id}")
    cert = CertificateService.get_by_id(db, certificate_id)
    if not cert:
        return {
            "found": False,
            "certificate_id": certificate_id,
            "message": f"Certificate {certificate_id} was not found in the operations database.",
        }

    return {
        "found": True,
        "certificate_id": cert.certificate_id,
        "customer_name": cert.customer_name,
        "domain": cert.domain,
        "certificate_type": cert.certificate_type,
        "issued_at": cert.issued_at.isoformat(),
        "expires_at": cert.expires_at.isoformat(),
        "status": cert.status,
        "revoked": cert.revoked,
        "revocation_date": cert.revocation_date.isoformat() if cert.revocation_date else None,
        "revocation_reason": cert.revocation_reason,
    }

def get_expiring_certificates_tool(db: Session, days: int = 30) -> Dict[str, Any]:
    """Return active certificates expiring within a specified number of days from today."""
    try:
        days_int = int(days)
    except (ValueError, TypeError):
        days_int = 30

    logger.info(f"Executing tool get_expiring_certificates for days: {days_int}")
    certs = CertificateService.get_expiring_certificates(db, days=days_int)
    return {
        "count": len(certs),
        "days_window": days_int,
        "current_date": date.today().isoformat(),
        "certificates": certs,
        "summary": f"Found {len(certs)} certificate(s) expiring within {days_int} days.",
    }

def get_certificates_expiring_between_tool(db: Session, start_date: str, end_date: str) -> Dict[str, Any]:
    """Return certificates expiring within a specified date range (YYYY-MM-DD)."""
    logger.info(f"Executing tool get_certificates_expiring_between: {start_date} to {end_date}")
    try:
        s_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        e_date = datetime.strptime(end_date, "%Y-%m-%d").date()
    except (ValueError, TypeError) as e:
        return {
            "error": f"Invalid date format: {e}. Expected YYYY-MM-DD.",
            "certificates": [],
            "count": 0,
        }

    certs = CertificateService.get_expiring_between(db, s_date, e_date)
    return {
        "count": len(certs),
        "start_date": start_date,
        "end_date": end_date,
        "certificates": certs,
        "summary": f"Found {len(certs)} certificate(s) expiring between {start_date} and {end_date}.",
    }

def check_revocation_tool(db: Session, certificate_id: str) -> Dict[str, Any]:
    """Check whether a certificate has been revoked and fetch revocation details."""
    logger.info(f"Executing tool check_revocation for ID: {certificate_id}")
    data = CertificateService.check_revocation(db, certificate_id)
    if not data:
        return {
            "found": False,
            "certificate_id": certificate_id,
            "message": f"Certificate {certificate_id} was not found in the operations database.",
        }

    return {
        "found": True,
        **data,
    }

def get_customer_certificates_tool(db: Session, customer_name: str) -> Dict[str, Any]:
    """Return all certificates belonging to a customer."""
    logger.info(f"Executing tool get_customer_certificates for customer: {customer_name}")
    certs = CertificateService.get_by_customer(db, customer_name)
    return {
        "customer_name": customer_name,
        "count": len(certs),
        "certificates": certs,
        "summary": f"Found {len(certs)} certificate(s) belonging to {customer_name}.",
    }
