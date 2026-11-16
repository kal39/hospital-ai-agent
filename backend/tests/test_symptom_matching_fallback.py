"""Tests for appointment department fallback guidance."""

import pytest

from app.services.symptom_matching import (
    suggest_department_or_general_medicine,
)


@pytest.mark.parametrize(
    ("message", "expected"),
    [
        ("I have a headache.", "General Medicine"),
        ("I feel dizzy.", "General Medicine"),
        ("I have a fever.", "General Medicine"),
        ("I have several symptoms.", "General Medicine"),
        ("I have a cough and ear pain.", "General Medicine"),
        ("I have palpitations and persistent anxiety.", "General Medicine"),
        ("I have no cough.", "General Medicine"),
        ("I do not have ear pain.", "General Medicine"),
        ("I have a persistent cough.", "Respiratory Clinic"),
        ("My heartbeat feels irregular.", "Cardiology"),
        ("I have a skin rash.", "Dermatology"),
    ],
)
def test_appointment_guidance_uses_specialist_or_general_medicine(
    message, expected
):
    result = suggest_department_or_general_medicine(message)

    assert result is not None
    assert result["department"] == expected
    assert result["reason"]


@pytest.mark.parametrize(
    "message",
    [
        "",
        "   ",
        "I have chest pain.",
        "I have severe difficulty breathing.",
        "I suddenly lost my vision.",
        "I suddenly lost vision.",
        "I have sudden loss of vision.",
        "I have sudden vision loss.",
        "I have slurred speech.",
        "I am coughing blood.",
    ],
)
def test_empty_or_potentially_urgent_messages_do_not_get_routine_fallback(
    message,
):
    assert suggest_department_or_general_medicine(message) is None
