"""Regression tests for bilingual medical safety checks."""

from app.services.safety import evaluate_safety


def test_amharic_kidney_pain_and_urinary_difficulty_is_flagged():
    result = evaluate_safety(
        "ኩላሊቴም ያመኛል ሽንት ያስቸገረኛል",
        "am",
    )

    assert result["blocked"] is True
    assert result["urgent"] is False
    assert result["message"]
    assert "ዛሬውኑ" in result["message"]


def test_amharic_frequent_urination_and_kidney_pain_is_flagged():
    result = evaluate_safety(
        "ኩላሊቴም ያመኛል ቶሎ ቶሎ ሸ",
        "am",
    )

    assert result["blocked"] is True
    assert result["message"]


def test_english_kidney_pain_and_frequent_urination_is_flagged():
    result = evaluate_safety(
        "My kidney hurts and I am urinating frequently.",
        "en",
    )

    assert result["blocked"] is True
    assert result["urgent"] is False
    assert result["message"]
    assert "preferably today" in result["message"]


def test_chest_pain_is_marked_urgent():
    result = evaluate_safety(
        "I have chest pain.",
        "en",
    )

    assert result["blocked"] is True
    assert result["urgent"] is True
    assert result["message"]


def test_ordinary_medication_question_is_not_blocked():
    result = evaluate_safety(
        "Please explain my medications.",
        "en",
    )

    assert result["blocked"] is False
    assert result["urgent"] is False
    assert result["message"] is None


def test_negated_kidney_and_urinary_symptoms_are_not_blocked():
    result = evaluate_safety(
        "I do not have kidney pain, and I have no urinary problems. "
        "Please explain my latest lab results.",
        "en",
    )

    assert result["blocked"] is False
    assert result["urgent"] is False
    assert result["message"] is None