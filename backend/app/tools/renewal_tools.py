"""Deterministic renewal tool implementations called by the AI agent."""
from typing import Any, Dict
from sqlalchemy.orm import Session
from app.services.renewal_service import RenewalService, RenewalValidationError
from app.utils.logger import logger

def create_renewal_request_tool(
    db: Session,
    certificate_id: str,
    requested_by: str = "ops-agent"
) -> Dict[str, Any]:
    """
    Action Tool: Validate certificate state and generate a renewal request record.
    Checks:
    - Certificate exists
    - Certificate is not already revoked
    - No active renewal request already exists
    """
    logger.info(f"Executing action tool create_renewal_request for cert: {certificate_id}")
    try:
        result = RenewalService.create_renewal(db, certificate_id, requested_by=requested_by)
        return {
            "success": True,
            "request_id": result["request_id"],
            "certificate_id": result["certificate_id"],
            "customer_name": result["customer_name"],
            "status": result["status"],
            "requested_at": result["requested_at"],
            "message": f"Renewal request {result['request_id']} generated successfully for certificate {result['certificate_id']}.",
        }
    except RenewalValidationError as e:
        logger.warning(f"Renewal validation failed for {certificate_id}: {e.message}")
        return {
            "success": False,
            "certificate_id": certificate_id,
            "error": e.message,
            "message": e.message,
        }
    except Exception as e:
        logger.error(f"Unexpected error in create_renewal_request: {e}")
        return {
            "success": False,
            "certificate_id": certificate_id,
            "error": f"Internal error during renewal: {str(e)}",
            "message": f"Unable to create renewal request for {certificate_id} due to an internal error.",
        }
