
"""Tests for the hospital agent safety checks."""

from app.services.safety import (
    evaluate_safety,
    suggest_care_case_priority,
)


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

def test_negated_chest_pain_is_not_flagged_as_urgent():
    result = evaluate_safety("I have no chest pain", "en")

    assert result["blocked"] is False
    assert result["urgent"] is False


def test_negated_emergency_symptom_list_is_not_flagged_as_urgent():
    result = evaluate_safety(
        "I feel dizzy, but I have no chest pain, difficulty breathing, "
        "fainting, weakness, or trouble speaking.",
        "en",
    )

    assert result["blocked"] is False
    assert result["urgent"] is False
    assert result["message"] is not None
    assert "dizziness" in result["message"].lower()


def test_positive_symptom_after_negated_symptom_is_still_urgent():
    result = evaluate_safety(
        "I have no chest pain, but I have difficulty breathing.",
        "en",
    )

    assert result["blocked"] is True
    assert result["urgent"] is True


def test_urgent_symptom_in_a_later_sentence_is_still_detected():
    result = evaluate_safety(
        "I have no chest pain. I have difficulty breathing.",
        "en",
    )

    assert result["blocked"] is True
    assert result["urgent"] is True


def test_additional_emergency_symptoms_are_flagged():
    examples = [
        "I have severe chest pressure and cold sweats.",
        "My mother's face is drooping and she cannot speak clearly.",
        "My child is having a seizure.",
        "My child is bleeding heavily.",
        "My father suddenly collapsed and is unconscious.",
        "I accidentally took too many tablets and feel dizzy.",
    ]

    for message in examples:
        result = evaluate_safety(message, "en")
        assert result["blocked"] is True, message
        assert result["urgent"] is True, message
        assert "immediate medical attention" in result["message"].lower()


def test_negated_new_emergency_symptoms_are_not_flagged():
    result = evaluate_safety(
        "I have no chest pressure, no facial drooping, and no trouble speaking.",
        "en",
    )

    assert result["blocked"] is False
    assert result["urgent"] is False

def test_historical_chest_pain_that_has_resolved_is_not_urgent():
    result = evaluate_safety(
        "I had chest pain last month, but I feel fine now.",
        "en",
    )

    assert result["blocked"] is False
    assert result["urgent"] is False


def test_historical_chest_pain_from_yesterday_is_not_urgent_when_resolved():
    result = evaluate_safety(
        "I experienced chest pain yesterday, but it has stopped.",
        "en",
    )

    assert result["blocked"] is False
    assert result["urgent"] is False


def test_current_chest_pain_after_historical_mention_is_still_urgent():
    result = evaluate_safety(
        "I had chest pain last month, but I have severe chest pain right now.",
        "en",
    )

    assert result["blocked"] is True
    assert result["urgent"] is True


def test_current_breathing_difficulty_after_old_chest_pain_is_urgent():
    result = evaluate_safety(
        "I had chest pain a week ago, but I am having difficulty breathing now.",
        "en",
    )

    assert result["blocked"] is True
    assert result["urgent"] is True



def test_present_perfect_chest_pain_is_still_urgent() -> None:
    result = evaluate_safety(
        "I have had severe chest pain for two hours.",
        "en",
    )

    assert result["blocked"] is True
    assert result["urgent"] is True


def test_ongoing_symptom_that_started_yesterday_is_still_urgent() -> None:
    result = evaluate_safety(
        "I have chest pain that started yesterday and is still happening.",
        "en",
    )

    assert result["blocked"] is True
    assert result["urgent"] is True


def test_recurring_chest_pain_after_old_episode_is_urgent() -> None:
    result = evaluate_safety(
        "I had chest pain last month, and I have chest pain again now.",
        "en",
    )

    assert result["blocked"] is True
    assert result["urgent"] is True


def test_resolved_historical_chest_pain_is_not_urgent() -> None:
    result = evaluate_safety(
        "I had chest pain yesterday, but it has completely stopped.",
        "en",
    )

    assert result["blocked"] is False
    assert result["urgent"] is False


def test_priority_reasons_are_returned_in_amharic() -> None:
    examples = [
        ("I have severe chest pain.", "emergency"),
        ("I feel dizzy.", "urgent"),
        ("Please explain my lab results.", "routine_review"),
    ]

    for message, expected_priority in examples:
        result = suggest_care_case_priority(message, "am")

        assert result["prioritySuggestion"] == expected_priority
        assert any(0x1200 <= ord(char) <= 0x137F for char in result["priorityReason"])
        assert "automated routing suggestion" not in result["priorityReason"]



def test_chest_pain_since_yesterday_is_still_urgent() -> None:
    result = evaluate_safety(
        "I have had chest pain since yesterday.",
        "en",
    )

    assert result["blocked"] is True
    assert result["urgent"] is True
