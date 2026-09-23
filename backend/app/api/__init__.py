"""API routes package."""
from fastapi import APIRouter
from app.api.certificates import router as certificates_router
from app.api.renewals import router as renewals_router
from app.api.agent import router as agent_router

api_router = APIRouter(prefix="/api")
api_router.include_router(certificates_router, prefix="/certificates", tags=["Certificates"])
api_router.include_router(renewals_router, prefix="/renewals", tags=["Renewals"])
api_router.include_router(agent_router, prefix="/agent", tags=["Agent"])

__all__ = ["api_router"]
