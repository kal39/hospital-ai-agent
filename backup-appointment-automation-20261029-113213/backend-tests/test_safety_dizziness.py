"""Regression tests for dizziness-related medical safety."""

from app.services.safety import evaluate_safety


def test_dizziness_after_medication_gets_specific_guidance():
    result = evaluate_safety(
        "I feel dizzy after taking my medication. "
        "Should I stop taking it or change the dose?",
        "en",
    )

    assert result["blocked"] is True
    assert result["urgent"] is False
    assert result["message"] is not None
    assert "dizzy" in result["message"].lower()
    assert "healthcare professional" in result["message"].lower()
    assert "Do not drive" in result["message"]
    assert "emergency medical care now" in result["message"]


def test_dizziness_in_amharic_gets_safety_guidance():
    result = evaluate_safety("ራሴ ዞረኝ", "am")

    assert result["blocked"] is True
    assert result["urgent"] is False
    assert result["message"] is not None
    assert "ማዞር" in result["message"]


def test_chest_pain_with_dizziness_still_takes_urgent_priority():
    result = evaluate_safety("I feel dizzy and have chest pain.", "en")

    assert result["blocked"] is True
    assert result["urgent"] is True
    assert result["message"] is not None
    assert "immediate medical attention" in result["message"]