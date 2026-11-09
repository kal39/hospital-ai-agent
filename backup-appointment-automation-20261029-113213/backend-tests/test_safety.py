
"""Tests for the hospital agent safety checks."""

from app.services.safety import evaluate_safety


def test_normal_lab_question_is_not_blocked() -> None:
    result = evaluate_safety("Please explain my lab results")

    assert result["blocked"] is False
    assert result["urgent"] is False
    assert result["message"] is None


def test_medication_stopping_request_is_blocked() -> None:
    result = evaluate_safety(
        "Should I stop taking my medication?",
        "en",
    )

    assert result["blocked"] is True
    assert result["urgent"] is False
    assert result["message"] is not None
    assert "care team" in result["message"]


def test_chest_pain_is_flagged_as_urgent() -> None:
    result = evaluate_safety("I have chest pain", "en")

    assert result["blocked"] is True
    assert result["urgent"] is True
    assert result["message"] is not None
    assert "immediate medical attention" in result["message"]


def test_urgent_match_takes_priority() -> None:
    result = evaluate_safety(
        "I have chest pain and should I stop taking my medication?",
        "en",
    )

    assert result["blocked"] is True
    assert result["urgent"] is True


def test_pattern_matching_is_case_insensitive() -> None:
    result = evaluate_safety("I HAVE CHEST PAIN", "en")

    assert result["blocked"] is True
    assert result["urgent"] is True
