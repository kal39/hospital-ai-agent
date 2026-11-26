
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

def test_historical_symptom_with_time_reference_before_symptom():
    result = evaluate_safety(
        "Yesterday I had chest pain, but it went away.",
        "en",
    )

    assert result["blocked"] is False
    assert result["urgent"] is False


def test_resolved_symptom_without_explicit_historical_time_is_not_urgent():
    result = evaluate_safety(
        "I had chest pain, but it has completely stopped.",
        "en",
    )

    assert result["blocked"] is False
    assert result["urgent"] is False


def test_current_breathing_emergency_after_historical_chest_pain_is_urgent():
    result = evaluate_safety(
        "I had chest pain yesterday, but now I cannot breathe.",
        "en",
    )

    assert result["blocked"] is True
    assert result["urgent"] is True


def test_gasping_for_air_is_flagged_as_urgent():
    result = evaluate_safety("I am gasping for air.", "en")

    assert result["blocked"] is True
    assert result["urgent"] is True


def test_possible_heart_attack_is_flagged_as_urgent():
    result = evaluate_safety("I think I am having a heart attack.", "en")

    assert result["blocked"] is True
    assert result["urgent"] is True


def test_sudden_one_sided_weakness_is_flagged_as_urgent():
    result = evaluate_safety(
        "One side of my body suddenly became weak.",
        "en",
    )

    assert result["blocked"] is True
    assert result["urgent"] is True


def test_severe_allergic_reaction_with_tongue_swelling_is_flagged():
    result = evaluate_safety(
        "My tongue is swelling and I am struggling to breathe.",
        "en",
    )

    assert result["blocked"] is True
    assert result["urgent"] is True



def test_additional_emergency_language_variations_are_flagged():
    examples = [
        "My breathing is getting worse.",
        "I can't catch my breath.",
        "I am struggling to catch my breath.",
        "One side of my face suddenly feels numb.",
        "My right arm suddenly went weak.",
        "My throat is closing up.",
        "My lips are swelling and I feel faint.",
        "I am vomiting blood.",
        "He stopped breathing.",
    ]

    for message in examples:
        result = evaluate_safety(message, "en")
        assert result["blocked"] is True, message
        assert result["urgent"] is True, message


def test_new_emergency_patterns_respect_explicit_negation():
    examples = [
        "I have no throat closing.",
        "I have no swollen lips.",
        "I have no difficulty catching my breath.",
    ]

    for message in examples:
        result = evaluate_safety(message, "en")
        assert result["blocked"] is False, message
        assert result["urgent"] is False, message


def test_new_emergency_patterns_respect_resolved_historical_symptoms():
    examples = [
        "Yesterday, my throat was closing, but it has completely resolved.",
        "Yesterday, my lips were swelling, but the swelling has completely stopped.",
    ]

    for message in examples:
        result = evaluate_safety(message, "en")
        assert result["blocked"] is False, message
        assert result["urgent"] is False, message


def test_regression_not_experiencing_chest_pain_is_not_urgent():
    result = evaluate_safety(
        "I am not experiencing chest pain.",
        "en",
    )

    assert result["blocked"] is False
    assert result["urgent"] is False


def test_regression_historical_chest_pain_not_returned_is_not_urgent():
    result = evaluate_safety(
        "I had chest pain yesterday, but it has not returned.",
        "en",
    )

    assert result["blocked"] is False
    assert result["urgent"] is False


def test_regression_current_breathing_difficulty_after_historical_symptom_is_urgent():
    result = evaluate_safety(
        "I had chest pain yesterday, and I am having difficulty breathing now.",
        "en",
    )

    assert result["blocked"] is True
    assert result["urgent"] is True


def test_regression_current_symptom_is_not_suppressed_by_old_resolved_symptom():
    result = evaluate_safety(
        "I had chest pain yesterday, but it has not returned. "
        "I am having difficulty breathing now.",
        "en",
    )

    assert result["blocked"] is True
    assert result["urgent"] is True

def test_sudden_inability_to_get_words_out_is_flagged_as_urgent():
    result = evaluate_safety(
        "I suddenly can't get my words out.",
        "en",
    )

    assert result["blocked"] is True
    assert result["urgent"] is True


def test_sudden_garbled_speech_is_flagged_as_urgent():
    result = evaluate_safety(
        "My speech suddenly became garbled.",
        "en",
    )

    assert result["blocked"] is True
    assert result["urgent"] is True


def test_sudden_loss_of_vision_in_one_eye_is_flagged_as_urgent():
    result = evaluate_safety(
        "I suddenly lost vision in my right eye.",
        "en",
    )

    assert result["blocked"] is True
    assert result["urgent"] is True


def test_worsening_breathlessness_is_flagged_as_urgent():
    result = evaluate_safety(
        "I am becoming more and more breathless.",
        "en",
    )

    assert result["blocked"] is True
    assert result["urgent"] is True


def test_isolated_heart_racing_does_not_alone_trigger_emergency_rule():
    result = evaluate_safety(
        "My heart is racing.",
        "en",
    )

    assert result["urgent"] is False


def test_sudden_blindness_in_one_eye_is_flagged_as_urgent():
    result = evaluate_safety(
        "I suddenly went blind in my right eye.",
        "en",
    )
    assert result["blocked"] is True
    assert result["urgent"] is True


def test_inability_to_see_out_of_one_eye_is_flagged_as_urgent():
    result = evaluate_safety(
        "I can't see out of my left eye.",
        "en",
    )
    assert result["blocked"] is True
    assert result["urgent"] is True


def test_sudden_numbness_in_one_arm_is_flagged_as_urgent():
    result = evaluate_safety(
        "My left arm suddenly went numb.",
        "en",
    )
    assert result["blocked"] is True
    assert result["urgent"] is True


def test_sudden_one_sided_body_numbness_is_flagged_as_urgent():
    result = evaluate_safety(
        "Suddenly, one side of my body feels numb.",
        "en",
    )
    assert result["blocked"] is True
    assert result["urgent"] is True


def test_fainting_is_flagged_as_urgent():
    result = evaluate_safety(
        "I fainted a few minutes ago.",
        "en",
    )
    assert result["blocked"] is True
    assert result["urgent"] is True


def test_sudden_loss_of_consciousness_is_flagged_as_urgent():
    result = evaluate_safety(
        "I suddenly passed out.",
        "en",
    )
    assert result["blocked"] is True
    assert result["urgent"] is True


def test_worst_headache_of_life_is_flagged_as_urgent():
    result = evaluate_safety(
        "This is the worst headache of my life.",
        "en",
    )
    assert result["blocked"] is True
    assert result["urgent"] is True


def test_explicit_denial_of_fainting_does_not_trigger_emergency():
    result = evaluate_safety(
        "I did not faint.",
        "en",
    )
    assert result["blocked"] is False
    assert result["urgent"] is False


def test_remote_history_of_fainting_does_not_trigger_emergency():
    result = evaluate_safety(
        "I fainted many years ago, but I am fine now.",
        "en",
    )
    assert result["blocked"] is False
    assert result["urgent"] is False


def test_ordinary_headache_does_not_trigger_emergency():
    result = evaluate_safety(
        "I have a mild headache today.",
        "en",
    )
    assert result["blocked"] is False
    assert result["urgent"] is False


def test_chronic_numbness_without_sudden_onset_does_not_trigger_emergency():
    result = evaluate_safety(
        "I have had mild numbness in both feet for several months.",
        "en",
    )
    assert result["blocked"] is False
    assert result["urgent"] is False

def test_feeling_faint_alone_does_not_trigger_emergency():
    result = evaluate_safety("I feel faint.", "en")
    assert result["blocked"] is False
    assert result["urgent"] is False

def test_sudden_confusion_is_flagged_as_urgent():
    result = evaluate_safety(
        "I suddenly became confused and cannot think clearly.",
        "en",
    )
    assert result["blocked"] is True
    assert result["urgent"] is True


def test_sudden_inability_to_understand_speech_is_flagged_as_urgent():
    result = evaluate_safety(
        "I suddenly cannot understand what people are saying.",
        "en",
    )
    assert result["blocked"] is True
    assert result["urgent"] is True


def test_sudden_loss_of_coordination_is_flagged_as_urgent():
    result = evaluate_safety(
        "I suddenly cannot walk straight and keep losing my balance.",
        "en",
    )
    assert result["blocked"] is True
    assert result["urgent"] is True


def test_longstanding_balance_problems_do_not_trigger_emergency():
    result = evaluate_safety(
        "I have had mild balance problems for several years.",
        "en",
    )
    assert result["blocked"] is False
    assert result["urgent"] is False


def test_ordinary_forgetfulness_does_not_trigger_emergency():
    result = evaluate_safety(
        "I sometimes forget where I put my keys.",
        "en",
    )
    assert result["blocked"] is False
    assert result["urgent"] is False

def test_sudden_double_vision_is_flagged_as_urgent():
    result = evaluate_safety(
        "I suddenly have double vision.",
        "en",
    )
    assert result["blocked"] is True
    assert result["urgent"] is True


def test_sudden_difficulty_swallowing_is_flagged_as_urgent():
    result = evaluate_safety(
        "I suddenly cannot swallow properly.",
        "en",
    )
    assert result["blocked"] is True
    assert result["urgent"] is True


def test_sudden_severe_dizziness_with_inability_to_stay_upright_is_flagged():
    result = evaluate_safety(
        "I suddenly feel severely dizzy and cannot stay upright.",
        "en",
    )
    assert result["blocked"] is True
    assert result["urgent"] is True


def test_chronic_mild_dizziness_does_not_trigger_emergency():
    result = evaluate_safety(
        "I have had mild dizziness on and off for several months.",
        "en",
    )
    assert result["blocked"] is False
    assert result["urgent"] is False


def test_longstanding_swallowing_difficulty_does_not_trigger_emergency():
    result = evaluate_safety(
        "I have had difficulty swallowing for several years.",
        "en",
    )
    assert result["blocked"] is False
    assert result["urgent"] is False

def test_third_person_sudden_speech_difficulty_is_flagged():
    result = evaluate_safety(
        "My father suddenly cannot get his words out.",
        "en",
    )
    assert result["blocked"] is True
    assert result["urgent"] is True


def test_third_person_sudden_double_vision_is_flagged():
    result = evaluate_safety(
        "My mother suddenly has double vision.",
        "en",
    )
    assert result["blocked"] is True
    assert result["urgent"] is True


def test_negated_third_person_stroke_symptom_is_not_flagged():
    result = evaluate_safety(
        "My father does not have sudden difficulty speaking.",
        "en",
    )
    assert result["blocked"] is False
    assert result["urgent"] is False


def test_resolved_historical_third_person_stroke_symptom_is_not_flagged():
    result = evaluate_safety(
        "My mother suddenly had double vision yesterday, but it has completely resolved.",
        "en",
    )
    assert result["blocked"] is False
    assert result["urgent"] is False


def test_current_third_person_symptom_after_old_resolved_episode_is_flagged():
    result = evaluate_safety(
        "My father had chest pain yesterday, but it stopped. "
        "Now he suddenly cannot understand what people are saying.",
        "en",
    )
    assert result["blocked"] is True
    assert result["urgent"] is True

def test_resolved_double_vision_that_returns_is_flagged():
    result = evaluate_safety(
        "My mother suddenly had double vision yesterday. "
        "It has completely resolved, but it has returned now.",
        "en",
    )
    assert result["blocked"] is True
    assert result["urgent"] is True

def test_resolved_double_vision_not_returned_is_not_flagged():
    result = evaluate_safety(
        "My mother suddenly had double vision yesterday. "
        "It has completely resolved, and it has not returned.",
        "en",
    )
    assert result["blocked"] is False
    assert result["urgent"] is False

def test_unrelated_rash_recurrence_does_not_reactivate_old_double_vision():
    result = evaluate_safety(
        "My mother suddenly had double vision yesterday. "
        "Her mild rash has completely resolved, but it has returned now.",
        "en",
    )
    assert result["blocked"] is False
    assert result["urgent"] is False

def test_explicitly_restated_double_vision_recurrence_is_flagged():
    result = evaluate_safety(
        "My mother suddenly had double vision yesterday. "
        "The double vision completely resolved, but the double vision "
        "has returned now.",
        "en",
    )
    assert result["blocked"] is True
    assert result["urgent"] is True
