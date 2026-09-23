"""API router for certificate renewals."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.renewal_service import RenewalService, RenewalValidationError
from app.schemas.renewal import RenewalCreate, RenewalResponse

router = APIRouter()

@router.post("", response_model=RenewalResponse, status_code=status.HTTP_201_CREATED, summary="Create a renewal request")
def create_renewal_request(payload: RenewalCreate, db: Session = Depends(get_db)):
    """
    Generate a new renewal request for a certificate.
    Enforces validation checks:
    - Certificate exists
    - Certificate is not revoked
    - No active renewal request already exists
    """
    try:
        result = RenewalService.create_renewal(
            db=db,
            certificate_id=payload.certificate_id,
            requested_by=payload.requested_by,
        )
        return result
    except RenewalValidationError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create renewal request: {str(e)}"
        )

@router.get("", response_model=List[RenewalResponse], summary="List all renewal requests")
def list_renewal_requests(db: Session = Depends(get_db)):
    """List all submitted certificate renewal requests."""
    return RenewalService.list_all_renewals(db)
