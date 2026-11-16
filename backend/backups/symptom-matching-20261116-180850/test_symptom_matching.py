"""Tests for conservative symptom-to-department suggestions."""

import pytest

from app.services.symptom_matching import suggest_department


@pytest.mark.parametrize(
    ("message", "expected_department"),
    [
        (
            "I've had a persistent cough for five days.",
            "Respiratory Clinic",
        ),
        (
            "I have an ongoing cough.",
            "Respiratory Clinic",
        ),
        (
            "I've been coughing for 3 weeks.",
            "Respiratory Clinic",
        ),
        (
            "I have ear pain.",
            "ENT",
        ),
        (
            "I've noticed hearing loss.",
            "ENT",
        ),
        (
            "I have a skin rash.",
            "Dermatology",
        ),
        (
            "I have an itchy rash.",
            "Dermatology",
        ),
    ],
)
def test_recognized_symptoms_return_tentative_department(
    message,
    expected_department,
):
    result = suggest_department(message)

    assert result is not None
    assert result["department"] == expected_department
    assert result["reason"]


@pytest.mark.parametrize(
    "message",
    [
        "",
        "I have a cough.",
        "I have a headache.",
        "I feel dizzy.",
        "I have stomach discomfort.",
        "I have several symptoms.",
        "I have no cough.",
        "I do not have ear pain.",
        "I have no skin rash.",
        "I have a persistent cough and ear pain.",
    ],
)
def test_unclear_negated_or_multiple_symptoms_return_no_suggestion(message):
    assert suggest_department(message) is None


def test_matching_is_case_insensitive():
    result = suggest_department("I HAVE A PERSISTENT COUGH")

    assert result is not None
    assert result["department"] == "Respiratory Clinic"


def test_empty_and_non_string_inputs_return_no_suggestion():
    assert suggest_department("") is None
    assert suggest_department("   ") is None
    assert suggest_department(None) is None
