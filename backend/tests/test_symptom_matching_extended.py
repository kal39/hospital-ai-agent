"""Expanded phrase-coverage tests for all supported departments."""

import pytest

from app.services.symptom_matching import (
    suggest_department,
    suggest_department_or_general_medicine,
)


@pytest.mark.parametrize(
    ("message", "department"),
    [
        ("I need an annual physical.", "General Medicine"),
        ("I want a primary care consultation.", "General Medicine"),
        ("I need a general health assessment.", "General Medicine"),
        ("I need a routine medical examination.", "General Medicine"),

        ("I have had an ongoing cough.", "Respiratory Clinic"),
        ("My cough has lasted three weeks.", "Respiratory Clinic"),
        ("I need an asthma review.", "Respiratory Clinic"),
        ("I have recurring wheezing.", "Respiratory Clinic"),

        ("My heart keeps racing.", "Cardiology"),
        ("I experience a fluttering heartbeat.", "Cardiology"),
        ("I have skipped heartbeats.", "Cardiology"),
        ("I need a palpitations follow-up.", "Cardiology"),

        ("I have hives.", "Dermatology"),
        ("I have recurring skin irritation.", "Dermatology"),
        ("I have a scalp problem.", "Dermatology"),
        ("I need a review for persistent acne.", "Dermatology"),

        ("I have recurring headaches.", "Neurology"),
        ("I have numbness in my feet.", "Neurology"),
        ("I have a persistent tremor.", "Neurology"),
        ("I need a migraine follow-up.", "Neurology"),

        ("I have persistent back pain.", "Orthopedics"),
        ("My joints feel stiff.", "Orthopedics"),
        ("I have elbow joint pain.", "Orthopedics"),
        ("I need a sports injury follow-up.", "Orthopedics"),

        ("I need a child health assessment.", "Pediatrics"),
        ("My infant needs a check-up.", "Pediatrics"),
        ("I need child growth monitoring.", "Pediatrics"),
        ("My child needs a development assessment.", "Pediatrics"),

        ("I have missed periods.", "Gynecology"),
        ("I need a menstrual health consultation.", "Gynecology"),
        ("I have changes in my menstrual cycles.", "Gynecology"),
        ("I need a women's health check-up.", "Gynecology"),

        ("I have red eyes.", "Ophthalmology"),
        ("My eyes are watery.", "Ophthalmology"),
        ("I have persistent eye irritation.", "Ophthalmology"),
        ("I need a vision assessment.", "Ophthalmology"),

        ("I have tooth decay.", "Dental"),
        ("I have cavities.", "Dental"),
        ("I need a dental cleaning.", "Dental"),
        ("I have a broken tooth.", "Dental"),

        ("I have a sore throat.", "ENT"),
        ("I have nasal congestion.", "ENT"),
        ("I need a hearing assessment.", "ENT"),
        ("I have a hearing problem.", "ENT"),
        ("I have hearing problems.", "ENT"),
        ("I have trouble hearing.", "ENT"),
        ("I have a problem with my hearing.", "ENT"),
        ("I have recurring ear infections.", "ENT"),

        ("I have persistent constipation.", "Gastroenterology"),
        ("I have recurring diarrhea.", "Gastroenterology"),
        ("I need a nausea follow-up.", "Gastroenterology"),
        ("I have persistent indigestion.", "Gastroenterology"),
        ("I've been having recurring stomach discomfort.", "Gastroenterology"),
        ("I have persistent stomach discomfort.", "Gastroenterology"),
        ("I have recurring digestive problems.", "Gastroenterology"),
        ("I have ongoing digestive issues.", "Gastroenterology"),

        ("I have urinary urgency.", "Urology"),
        ("I have difficulty urinating.", "Urology"),
        ("I need a urinary health consultation.", "Urology"),
        ("I have urinary frequency.", "Urology"),

        ("I have persistent stress.", "Psychiatry"),
        ("I need a depression follow-up.", "Psychiatry"),
        ("I need a mental wellness assessment.", "Psychiatry"),
        ("I have ongoing stress.", "Psychiatry"),

        ("I need a thyroid review.", "Endocrinology"),
        ("I need a hormone imbalance follow-up.", "Endocrinology"),
        ("I need diabetes management.", "Endocrinology"),
        ("I need a blood sugar review.", "Endocrinology"),

        ("I need a proteinuria follow-up.", "Nephrology"),
        ("I need a kidney health assessment.", "Nephrology"),
        ("I need a reduced kidney function review.", "Nephrology"),
        ("I need a chronic kidney disease follow-up.", "Nephrology"),
    ],
)
def test_expanded_phrases_suggest_expected_department(message, department):
    result = suggest_department(message)
    assert result is not None
    assert result["department"] == department
    assert result["reason"]


@pytest.mark.parametrize(
    "message",
    [
        "I have a cough and ear pain.",
        "I have a toothache and blurred vision.",
        "I have palpitations and persistent anxiety.",
        "I have a persistent cough and a skin rash.",
        "I have a sore throat and persistent heartburn.",
        "I have fever and tooth pain.",
        "I have chest pain.",
        "I have severe difficulty breathing.",
        "I suddenly lost my vision.",
        "I have sudden hearing loss.",
        "I have sudden loss of hearing.",
        "I suddenly lost my hearing.",
        "I have sudden weakness on one side.",
        "I have slurred speech.",
        "I am coughing blood.",
        "I have a headache.",
        "I feel dizzy.",
        "I have a fever.",
        "I have fatigue.",
        "I have nausea.",
        "I have body aches.",
    ],
)
def test_ambiguous_unsupported_or_urgent_phrases_return_none(message):
    assert suggest_department(message) is None


@pytest.mark.parametrize(
    ("message", "department"),
    [
        ("I have no cough, but I have ear pain.", "ENT"),
        ("I do not have a headache, but I have a toothache.", "Dental"),
        ("I have no rash, but I have blurred vision.", "Ophthalmology"),
        ("I have no palpitations, but I need a thyroid review.", "Endocrinology"),
        ("I have no fever. I need an asthma review.", "Respiratory Clinic"),
    ],
)
def test_negated_unrelated_symptom_does_not_block_positive_match(
    message, department
):
    result = suggest_department(message)
    assert result is not None
    assert result["department"] == department


@pytest.mark.parametrize(
    "message",
    [
        "I do not have ear pain.",
        "I have no toothache.",
        "I don't have blurred vision.",
        "I have no persistent anxiety.",
        "I do not have a thyroid condition.",
        "I have no cough.",
    ],
)
def test_negated_symptoms_do_not_produce_suggestions(message):
    assert suggest_department(message) is None


def test_case_insensitive_matching():
    result = suggest_department("I NEED A DENTAL CLEANING.")
    assert result is not None
    assert result["department"] == "Dental"


def test_non_string_and_empty_inputs_return_none():
    assert suggest_department("") is None
    assert suggest_department("   ") is None
    assert suggest_department(None) is None


@pytest.mark.parametrize(
    "message",
    [
        "I don't have blurred vision.",
        "I have no palpitations.",
        "I do not have a persistent cough.",
    ],
)
def test_negated_symptoms_do_not_trigger_general_medicine_fallback(message):
    assert suggest_department_or_general_medicine(message) is None


@pytest.mark.parametrize(
    ("message", "department"),
    [
        ("I have tooth pain.", "Dental"),
        ("I have a persistent cough.", "Respiratory Clinic"),
        ("My heartbeat feels irregular.", "Cardiology"),
        ("I have a headache.", "General Medicine"),
        ("I have fever and tooth pain.", "General Medicine"),
    ],
)
def test_positive_symptoms_keep_expected_fallback_department(
    message, department
):
    result = suggest_department_or_general_medicine(message)
    assert result is not None
    assert result["department"] == department
