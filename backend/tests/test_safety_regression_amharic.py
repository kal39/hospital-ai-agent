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



def test_amharic_chest_pain_is_flagged_as_emergency():
    result = evaluate_safety(
        "\u12e8\u12f0\u1228\u1275 \u1205\u1218\u121d \u12a0\u1208\u1265\u129d",
        "am",
    )

    assert result["blocked"] is True
    assert result["urgent"] is True
    assert result["message"]


def test_amharic_breathing_difficulty_is_flagged_as_emergency():
    result = evaluate_safety(
        "\u12e8\u1218\u1270\u1295\u1348\u1235 \u127d\u130d\u122d \u12a0\u1208\u1265\u129d",
        "am",
    )

    assert result["blocked"] is True
    assert result["urgent"] is True
    assert result["message"]


def test_amharic_inability_to_breathe_is_flagged_as_emergency():
    result = evaluate_safety(
        "\u1218\u1270\u1295\u1348\u1235 \u12a0\u120d\u127b\u120d\u12a9\u121d",
        "am",
    )

    assert result["blocked"] is True
    assert result["urgent"] is True
    assert result["message"]


def test_amharic_severe_bleeding_is_flagged_as_emergency():
    result = evaluate_safety(
        "\u12a8\u1263\u12f5 \u12f0\u121d \u1218\u134d\u1230\u1235 \u12a0\u1208",
        "am",
    )

    assert result["blocked"] is True
    assert result["urgent"] is True
    assert result["message"]


def test_amharic_emergency_response_uses_amharic_message():
    result = evaluate_safety(
        "\u12e8\u12f0\u1228\u1275 \u1205\u1218\u121d \u12a0\u1208\u1265\u129d",
        "am",
    )

    assert result["blocked"] is True
    assert result["urgent"] is True
    assert "\u1218\u120d\u12d5\u12ad\u1275\u12ce" in result["message"]
    assert "Your message" not in result["message"]
