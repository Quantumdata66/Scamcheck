"""
Health check route.
"""

from fastapi import APIRouter
from app.schemas import HealthResponse

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="API Health Check",
    description="Returns the current operational status and version of the API."
)
def get_health() -> HealthResponse:
    """Return health status."""
    return HealthResponse(status="healthy", version="0.1.0")
