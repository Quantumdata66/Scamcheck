"""
Message detection route.
"""

from fastapi import APIRouter, Depends
from app.schemas import CheckRequest, CheckResponse
from app.services.detector import RulesBaselineDetector, get_detector_service

router = APIRouter(tags=["Detection"])


@router.post(
    "/check",
    response_model=CheckResponse,
    summary="Analyze Suspicious Message",
    description="Validates and analyzes a suspicious message, returning risk indicators and guidance."
)
def check_message(
    payload: CheckRequest,
    detector: RulesBaselineDetector = Depends(get_detector_service)
) -> CheckResponse:
    """Analyze the submitted message using the detection service."""
    return detector.analyze(payload.get_message_content())
