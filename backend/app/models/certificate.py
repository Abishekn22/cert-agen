"""Certificate SQLAlchemy model."""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, Date, DateTime
from app.database import Base

class Certificate(Base):
    __tablename__ = "certificates"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    certificate_id = Column(String(64), unique=True, index=True, nullable=False)
    customer_name = Column(String(128), index=True, nullable=False)
    domain = Column(String(255), index=True, nullable=False)
    certificate_type = Column(String(32), default="TLS", nullable=False)
    issued_at = Column(Date, nullable=False)
    expires_at = Column(Date, index=True, nullable=False)
    status = Column(String(32), default="ACTIVE", index=True, nullable=False)
    revoked = Column(Boolean, default=False, index=True, nullable=False)
    revocation_date = Column(Date, nullable=True)
    revocation_reason = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<Certificate {self.certificate_id} domain={self.domain} status={self.status}>"
