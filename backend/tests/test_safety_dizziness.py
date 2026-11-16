"""Regression tests for dizziness-related medical safety."""

from app.services.safety import DIZZINESS_MESSAGE_AM, evaluate_safety


def test_dizziness_alone_returns_non_blocking_guidance():
    result = evaluate_safety("I feel dizzy", "en")

    assert result["blocked"] is False
    assert result["urgent"] is False
    assert result["message"] is not None
    assert "healthcare professional" in result["message"].lower()
    assert "do not drive" in result["message"].lower()
    assert "emergency medical care now" in result["message"].lower()
    assert "after taking medication" not in result["message"].lower()


def test_dizziness_with_medication_change_request_is_blocked():
    result = evaluate_safety(
        "I feel dizzy after taking my medication. "
        "Should I stop taking it or change the dose?",
        "en",
    )

    assert result["blocked"] is True
    assert result["urgent"] is False
    assert result["message"] is not None
    assert "care team" in result["message"].lower()
    assert "independently" in result["message"].lower()
    assert "after taking medication" not in result["message"].lower()


def test_dizziness_in_amharic_gets_non_blocking_safety_guidance():
    result = evaluate_safety("\u121b\u12de\u122d", "am")

    assert result["blocked"] is False
    assert result["urgent"] is False
    assert result["message"] == DIZZINESS_MESSAGE_AM
    assert result["message"] is not None


def test_chest_pain_with_dizziness_still_takes_urgent_priority():
    result = evaluate_safety("I feel dizzy and have chest pain.", "en")

    assert result["blocked"] is True
    assert result["urgent"] is True
    assert result["message"] is not None
    assert "immediate medical attention" in result["message"]
