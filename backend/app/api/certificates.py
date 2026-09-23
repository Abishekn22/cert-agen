"""API router for certificate inspection and querying."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.certificate_service import CertificateService
from app.schemas.certificate import (
    CertificateResponse,
    CertificateExpiringItem,
    RevocationResponse,
)

router = APIRouter()

@router.get("/expiring", response_model=List[CertificateExpiringItem], summary="Get expiring certificates")
def get_expiring_certificates(
    days: int = Query(default=30, ge=1, le=365, description="Number of days to check for expiration"),
    db: Session = Depends(get_db),
):
    """Return active certificates expiring within the next N days."""
    certs = CertificateService.get_expiring_certificates(db, days=days)
    return certs

@router.get("/customer/{customer_name}", summary="Get certificates by customer")
def get_customer_certificates(customer_name: str, db: Session = Depends(get_db)):
    """Return all certificates belonging to a specific customer."""
    certs = CertificateService.get_by_customer(db, customer_name=customer_name)
    return certs

@router.get("/{certificate_id}/revocation", response_model=RevocationResponse, summary="Check revocation status")
def check_revocation(certificate_id: str, db: Session = Depends(get_db)):
    """Check revocation status, date, and reason for a certificate."""
    data = CertificateService.check_revocation(db, certificate_id=certificate_id)
    if not data:
        raise HTTPException(status_code=404, detail=f"Certificate {certificate_id} was not found.")
    return data

@router.get("/{certificate_id}", response_model=CertificateResponse, summary="Get certificate details")
def get_certificate_details(certificate_id: str, db: Session = Depends(get_db)):
    """Fetch complete certificate details by certificate ID."""
    cert = CertificateService.get_by_id(db, certificate_id=certificate_id)
    if not cert:
        raise HTTPException(status_code=404, detail=f"Certificate {certificate_id} was not found.")
    return cert
