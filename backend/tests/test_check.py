"""
Tests for the POST /check endpoint.
"""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_valid_check_request_succeeds():
    """Verify that a valid message payload returns 200 OK."""
    payload = {"message": "Urgent: your account has been locked. Verify identity immediately."}
    response = client.post("/check", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["risk_level"] in ["needs_verification", "high"]
    assert data["risk_label"] in ["Needs further verification", "Multiple warning signs detected"]


def test_empty_message_is_rejected():
    """Verify that an empty message string fails validation with 422 Unprocessable Entity."""
    payload = {"message": ""}
    response = client.post("/check", json=payload)
    assert response.status_code == 422


def test_whitespace_only_message_is_rejected():
    """Verify that a message containing only whitespace is rejected with 422."""
    payload = {"message": "   \n\t  \r  "}
    response = client.post("/check", json=payload)
    assert response.status_code == 422


def test_message_over_2000_characters_is_rejected():
    """Verify that a message exceeding 2000 characters is rejected with 422."""
    long_message = "x" * 2001
    payload = {"message": long_message}
    response = client.post("/check", json=payload)
    assert response.status_code == 422


def test_message_exactly_2000_characters_succeeds():
    """Verify that a message at exactly the 2000-character boundary succeeds."""
    boundary_message = "x" * 2000
    payload = {"message": boundary_message}
    response = client.post("/check", json=payload)
    assert response.status_code == 200


def test_missing_message_field_is_rejected():
    """Verify that a payload missing the required 'message' key is rejected with 422."""
    payload = {}
    response = client.post("/check", json=payload)
    assert response.status_code == 422


def test_invalid_data_type_is_rejected():
    """Verify that a non-string message value is rejected with 422."""
    payload = {"message": 12345}
    response = client.post("/check", json=payload)
    assert response.status_code == 422


def test_invalid_json_body_is_rejected():
    """Verify that non-JSON or invalid body content is rejected with 422."""
    response = client.post(
        "/check",
        content="not-json-content",
        headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 422


def test_check_returns_all_expected_fields():
    """Verify that the response contains all required fields and correct data types."""
    payload = {"message": "Please confirm your login details."}
    response = client.post("/check", json=payload)
    assert response.status_code == 200
    data = response.json()

    expected_fields = [
        "risk_level",
        "risk_label",
        "summary",
        "category",
        "explanation",
        "indicators",
        "safety_guidance"
    ]

    for field in expected_fields:
        assert field in data, f"Missing required response field: {field}"

    assert isinstance(data["risk_level"], str)
    assert isinstance(data["risk_label"], str)
    assert isinstance(data["summary"], str)
    assert data["category"] is None or isinstance(data["category"], str)
    assert isinstance(data["explanation"], str)
    assert isinstance(data["indicators"], list)
    assert isinstance(data["safety_guidance"], list)
