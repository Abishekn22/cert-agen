"""Renewal Pydantic schemas."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

class RenewalCreate(BaseModel):
    certificate_id: str = Field(..., description="ID of the certificate to renew")
    requested_by: str = Field(default="ops-agent", description="User or agent initiating renewal")

class RenewalResponse(BaseModel):
    request_id: str
    certificate_id: str
    customer_name: str
    requested_at: datetime
    status: str
    requested_by: str

    model_config = ConfigDict(from_attributes=True)
