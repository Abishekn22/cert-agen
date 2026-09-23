"""Service layer for certificate renewals with strict business rule validations."""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.certificate import Certificate
from app.models.renewal import RenewalRequest
from app.services.certificate_service import CertificateService
from app.utils.logger import logger

class RenewalValidationError(Exception):
    """Custom exception for renewal validation failures."""
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code

class RenewalService:
    @staticmethod
    def _generate_request_id(db: Session) -> str:
        """Generate formatted sequential ID: REN-YYYY-XXXX."""
        year = datetime.now(timezone.utc).year
        prefix = f"REN-{year}-"
        count = (
            db.query(func.count(RenewalRequest.id))
            .filter(RenewalRequest.request_id.like(f"{prefix}%"))
            .scalar() or 0
        )
        return f"{prefix}{count + 1:04d}"

    @staticmethod
    def get_by_request_id(db: Session, request_id: str) -> Optional[RenewalRequest]:
        """Fetch renewal request by request_id."""
        return db.query(RenewalRequest).filter(
            func.lower(RenewalRequest.request_id) == request_id.strip().lower()
        ).first()

    @staticmethod
    def get_active_renewal_for_cert(db: Session, certificate_id: str) -> Optional[RenewalRequest]:
        """Check if an active/pending renewal already exists for this certificate."""
        return db.query(RenewalRequest).filter(
            func.lower(RenewalRequest.certificate_id) == certificate_id.strip().lower(),
            RenewalRequest.status.in_(["PENDING", "APPROVED", "IN_PROGRESS"]),
        ).first()

    @staticmethod
    def list_all_renewals(db: Session) -> List[Dict[str, Any]]:
        """List all renewal requests ordered by requested_at desc."""
        records = db.query(RenewalRequest).order_by(RenewalRequest.requested_at.desc()).all()
        return [
            {
                "request_id": r.request_id,
                "certificate_id": r.certificate_id,
                "customer_name": r.customer_name,
                "requested_at": r.requested_at.isoformat(),
                "status": r.status,
                "requested_by": r.requested_by,
            }
            for r in records
        ]

    @staticmethod
    def create_renewal(db: Session, certificate_id: str, requested_by: str = "ops-agent") -> Dict[str, Any]:
        """
        Validate and create a renewal request for a certificate.
        Enforces:
        1. Certificate exists.
        2. Certificate is not revoked.
        3. No active renewal request already exists.
        """
        cert = CertificateService.get_by_id(db, certificate_id)
        if not cert:
            raise RenewalValidationError(
                f"Certificate {certificate_id} was not found.",
                status_code=404
            )

        if cert.revoked or cert.status == "REVOKED":
            reason_suffix = f" (Reason: {cert.revocation_reason})" if cert.revocation_reason else ""
            raise RenewalValidationError(
                f"Certificate {cert.certificate_id} is already revoked and cannot be renewed{reason_suffix}.",
                status_code=409
            )

        existing_renewal = RenewalService.get_active_renewal_for_cert(db, cert.certificate_id)
        if existing_renewal:
            raise RenewalValidationError(
                f"An active renewal request already exists for {cert.certificate_id} ({existing_renewal.request_id} with status '{existing_renewal.status}').",
                status_code=409
            )

        request_id = RenewalService._generate_request_id(db)
        renewal = RenewalRequest(
            request_id=request_id,
            certificate_id=cert.certificate_id,
            customer_name=cert.customer_name,
            requested_at=datetime.now(timezone.utc),
            status="PENDING",
            requested_by=requested_by,
        )

        db.add(renewal)
        db.commit()
        db.refresh(renewal)

        logger.info(f"Renewal created: {renewal.request_id} for cert {cert.certificate_id} ({cert.customer_name})")

        return {
            "request_id": renewal.request_id,
            "certificate_id": renewal.certificate_id,
            "customer_name": renewal.customer_name,
            "requested_at": renewal.requested_at.isoformat(),
            "status": renewal.status,
            "requested_by": renewal.requested_by,
        }
