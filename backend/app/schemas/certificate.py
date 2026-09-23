"""Certificate Pydantic schemas."""
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class CertificateBase(BaseModel):
    certificate_id: str
    customer_name: str
    domain: str
    certificate_type: str = "TLS"
    issued_at: date
    expires_at: date
    status: str = "ACTIVE"
    revoked: bool = False
    revocation_date: Optional[date] = None
    revocation_reason: Optional[str] = None

class CertificateCreate(CertificateBase):
    pass

class CertificateResponse(CertificateBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class CertificateExpiringItem(BaseModel):
    certificate_id: str
    customer_name: str
    domain: str
    certificate_type: str
    expires_at: date
    status: str
    days_remaining: int

class RevocationResponse(BaseModel):
    certificate_id: str
    revoked: bool
    revocation_date: Optional[date] = None
    revocation_reason: Optional[str] = None
    status: str
