"""RenewalRequest SQLAlchemy model."""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from app.database import Base

class RenewalRequest(Base):
    __tablename__ = "renewal_requests"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    request_id = Column(String(64), unique=True, index=True, nullable=False)
    certificate_id = Column(String(64), ForeignKey("certificates.certificate_id"), index=True, nullable=False)
    customer_name = Column(String(128), index=True, nullable=False)
    requested_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    status = Column(String(32), default="PENDING", index=True, nullable=False)
    requested_by = Column(String(128), default="ops-agent", nullable=False)

    def __repr__(self) -> str:
        return f"<RenewalRequest {self.request_id} cert={self.certificate_id} status={self.status}>"
