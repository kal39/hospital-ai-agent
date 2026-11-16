"""Tests for conservative symptom-to-department suggestions."""

import pytest

from app.services.symptom_matching import suggest_department


@pytest.mark.parametrize(
    ("message", "expected_department"),
    [
        ("I need a routine general check-up.", "General Medicine"),
        ("I've had a persistent cough for five days.", "Respiratory Clinic"),
        ("I have ongoing wheezing.", "Respiratory Clinic"),
        ("I have heart palpitations.", "Cardiology"),
        ("My heartbeat feels irregular.", "Cardiology"),
        ("I have a skin rash.", "Dermatology"),
        ("I have itchy eczema.", "Dermatology"),
        ("I have recurrent migraine attacks.", "Neurology"),
        ("I have tingling in my hands.", "Neurology"),
        ("I have knee joint pain.", "Orthopedics"),
        ("I have joint swelling.", "Orthopedics"),
        ("My child needs a wellness visit.", "Pediatrics"),
        ("My baby needs a check-up.", "Pediatrics"),
        ("I have irregular menstrual periods.", "Gynecology"),
        ("I have severe menstrual cramps.", "Gynecology"),
        ("I have blurred vision.", "Ophthalmology"),
        ("I need an eye examination.", "Ophthalmology"),
        ("I have a toothache.", "Dental"),
        ("My gums are bleeding.", "Dental"),
        ("I have ear pain.", "ENT"),
        ("I've noticed hearing loss.", "ENT"),
        ("I have persistent heartburn.", "Gastroenterology"),
        ("I have recurring acid reflux.", "Gastroenterology"),
        ("I have burning when urinating.", "Urology"),
        ("I have painful urination.", "Urology"),
        ("I've had persistent anxiety.", "Psychiatry"),
        ("I have frequent panic attacks.", "Psychiatry"),
        ("I need a thyroid follow-up.", "Endocrinology"),
        ("I need diabetes follow-up.", "Endocrinology"),
        ("I need a kidney function follow-up.", "Nephrology"),
        ("I have protein in my urine.", "Nephrology"),
    ],
)
def test_specific_symptoms_suggest_all_supported_departments(
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
        "   ",
        "I have a cough.",
        "I have a headache.",
        "I feel dizzy.",
        "I have stomach discomfort.",
        "I have several symptoms.",
        "I have a fever.",
        "I have back pain.",
        "I have chest pain.",
        "I have difficulty breathing.",
        "I have a cough and ear pain.",
        "I have a toothache and blurred vision.",
        "I have palpitations and persistent anxiety.",
        "I have a persistent cough and a skin rash.",
        "I have no cough.",
        "I do not have ear pain.",
        "I have no skin rash.",
        "I have no palpitations.",
        "I don't have blurred vision.",
        "I do not have a toothache.",
        "I have no burning when urinating.",
        "I have no persistent anxiety.",
    ],
)
def test_unclear_negated_urgent_or_multiple_symptoms_return_no_suggestion(
    message,
):
    assert suggest_department(message) is None


def test_matching_is_case_insensitive():
    result = suggest_department("I HAVE A PERSISTENT COUGH")

    assert result is not None
    assert result["department"] == "Respiratory Clinic"


def test_positive_symptom_after_negated_symptom_can_match():
    result = suggest_department(
        "I have no cough, but I have ear pain."
    )

    assert result is not None
    assert result["department"] == "ENT"


def test_negated_symptom_before_positive_symptom_in_later_sentence():
    result = suggest_department(
        "I have no cough. I have ear pain."
    )

    assert result is not None
    assert result["department"] == "ENT"


def test_empty_and_non_string_inputs_return_no_suggestion():
    assert suggest_department("") is None
    assert suggest_department("   ") is None
    assert suggest_department(None) is None
