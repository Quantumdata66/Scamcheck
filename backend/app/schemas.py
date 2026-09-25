"""
Pydantic schemas for request validation and response models.
"""

from typing import Any, List, Optional
from pydantic import BaseModel, Field, model_validator


class HealthResponse(BaseModel):
    """Response model for the GET /health endpoint."""
    status: str = Field(default="healthy", description="Current health status of the API")
    version: str = Field(default="0.1.0", description="API version")


class CheckRequest(BaseModel):
    """
    Request model for the POST /check endpoint.
    Accepts either 'text' (preferred for frontend) or 'message' (legacy/API contract).
    """
    text: Optional[str] = Field(
        default=None,
        description="The suspicious message text to analyze (max 2000 characters)."
    )
    message: Optional[str] = Field(
        default=None,
        description="Alternative field name for the suspicious message text."
    )

    @model_validator(mode="before")
    @classmethod
    def validate_content(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            raise ValueError("Request body must be a JSON object.")

        raw_text = data.get("text")
        if raw_text is None:
            raw_text = data.get("message")

        if raw_text is None:
            raise ValueError("A 'text' or 'message' field is required.")

        if not isinstance(raw_text, str):
            raise ValueError("Message content must be a string.")

        stripped = raw_text.strip()
        if not stripped:
            raise ValueError("Message cannot be empty or contain only whitespace.")

        if len(raw_text) > 2000:
            raise ValueError("Message exceeds maximum length of 2000 characters.")

        return {"text": raw_text, "message": raw_text}

    def get_message_content(self) -> str:
        """Return the validated message string."""
        return self.text or self.message or ""


class CheckResponse(BaseModel):
    """Response model for the POST /check endpoint."""
    risk_level: str = Field(
        default="needs_verification",
        description="Machine-readable risk classification (e.g., low, needs_verification, high)"
    )
    risk_label: str = Field(
        default="Needs further verification",
        description="Human-readable label for frontend display badge"
    )
    summary: str = Field(
        ...,
        description="Brief summary assessment of the message"
    )
    category: Optional[str] = Field(
        default=None,
        description="Identified scam category (e.g., bank_payment, fake_job, investment), or null"
    )
    explanation: str = Field(
        ...,
        description="Cautious contextual explanation of the assessment"
    )
    indicators: List[str] = Field(
        default_factory=list,
        description="List of detected risk indicators or warning signs"
    )
    safety_guidance: List[str] = Field(
        default_factory=list,
        description="Safe next steps and protective actions for the user"
    )
