"""Service layer for certificate operations."""
from datetime import date, timedelta
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.certificate import Certificate

class CertificateService:
    @staticmethod
    def get_by_id(db: Session, certificate_id: str) -> Optional[Certificate]:
        """Fetch certificate by its unique certificate_id (case-insensitive)."""
        return db.query(Certificate).filter(
            func.lower(Certificate.certificate_id) == certificate_id.strip().lower()
        ).first()

    @staticmethod
    def get_expiring_certificates(db: Session, days: int) -> List[Dict[str, Any]]:
        """
        Return active, non-revoked certificates expiring within the next N days.
        Calculations are strictly anchored to the current execution date.
        """
        today = date.today()
        cutoff_date = today + timedelta(days=days)

        certs = (
            db.query(Certificate)
            .filter(
                Certificate.expires_at >= today,
                Certificate.expires_at <= cutoff_date,
                Certificate.revoked.is_(False),
                Certificate.status != "REVOKED",
            )
            .order_by(Certificate.expires_at.asc())
            .all()
        )

        results = []
        for c in certs:
            days_left = (c.expires_at - today).days
            results.append({
                "certificate_id": c.certificate_id,
                "customer_name": c.customer_name,
                "domain": c.domain,
                "certificate_type": c.certificate_type,
                "issued_at": c.issued_at.isoformat(),
                "expires_at": c.expires_at.isoformat(),
                "status": c.status,
                "days_remaining": max(0, days_left),
            })
        return results

    @staticmethod
    def get_expiring_between(db: Session, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """Return active, non-revoked certificates expiring between two specific dates."""
        today = date.today()
        certs = (
            db.query(Certificate)
            .filter(
                Certificate.expires_at >= start_date,
                Certificate.expires_at <= end_date,
                Certificate.revoked.is_(False),
                Certificate.status != "REVOKED",
            )
            .order_by(Certificate.expires_at.asc())
            .all()
        )

        results = []
        for c in certs:
            days_left = (c.expires_at - today).days
            results.append({
                "certificate_id": c.certificate_id,
                "customer_name": c.customer_name,
                "domain": c.domain,
                "certificate_type": c.certificate_type,
                "issued_at": c.issued_at.isoformat(),
                "expires_at": c.expires_at.isoformat(),
                "status": c.status,
                "days_remaining": days_left,
            })
        return results

    @staticmethod
    def check_revocation(db: Session, certificate_id: str) -> Optional[Dict[str, Any]]:
        """Check revocation status, date, and reason for a certificate."""
        cert = CertificateService.get_by_id(db, certificate_id)
        if not cert:
            return None

        return {
            "certificate_id": cert.certificate_id,
            "revoked": bool(cert.revoked),
            "revocation_date": cert.revocation_date.isoformat() if cert.revocation_date else None,
            "revocation_reason": cert.revocation_reason,
            "status": cert.status,
            "customer_name": cert.customer_name,
            "domain": cert.domain,
        }

    @staticmethod
    def get_by_customer(db: Session, customer_name: str) -> List[Dict[str, Any]]:
        """Return all certificates belonging to a customer."""
        certs = (
            db.query(Certificate)
            .filter(func.lower(Certificate.customer_name) == customer_name.strip().lower())
            .order_by(Certificate.expires_at.asc())
            .all()
        )

        today = date.today()
        results = []
        for c in certs:
            days_left = (c.expires_at - today).days
            results.append({
                "certificate_id": c.certificate_id,
                "customer_name": c.customer_name,
                "domain": c.domain,
                "certificate_type": c.certificate_type,
                "issued_at": c.issued_at.isoformat(),
                "expires_at": c.expires_at.isoformat(),
                "status": c.status,
                "revoked": c.revoked,
                "days_remaining": days_left,
            })
        return results
