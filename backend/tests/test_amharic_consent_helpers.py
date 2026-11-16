import pytest
from app.services.agent import (
    _assistant_asked_for_appointment_consent,
    _consent_cancelled_message,
    _consent_clarification_message,
    _consent_decision,
    _consent_information_message,
    _consent_question,
)


def test_amharic_yes_grants_search_consent():
    assert _consent_decision("አዎ") == "yes"
    assert _consent_decision("አዎ።") == "yes"
    assert _consent_decision("እሺ") == "yes"


def test_amharic_no_declines_search_consent():
    assert _consent_decision("አይ") == "no"
    assert _consent_decision("አይ።") == "no"
    assert _consent_decision("አልፈልግም") == "no"


def test_ambiguous_answers_do_not_grant_consent():
    assert _consent_decision("አዎ፣ ግን ነገ") == "unclear"
    assert _consent_decision("Yes, but tomorrow") == "unclear"
    assert _consent_decision("maybe") == "unclear"


def test_english_consent_still_works():
    assert _consent_decision("Yes") == "yes"
    assert _consent_decision("No") == "no"


def test_amharic_consent_question_is_localized():
    message = _consent_question("am")
    assert "አዎ" in message
    assert "አይ" in message
    assert "Would you like" not in message


def test_english_consent_question_remains_in_english():
    message = _consent_question("en")
    assert "Would you like" in message
    assert "አዎ" not in message


def test_amharic_follow_up_messages_are_localized():
    assert "አዎ" in _consent_clarification_message("am")
    assert "አይ" in _consent_information_message("am")
    assert "አልፈልግም" in _consent_cancelled_message("am")


def test_english_follow_up_messages_remain_in_english():
    assert "Please reply yes" in _consent_clarification_message("en")
    assert "I would use information" in _consent_information_message("en")
    assert "I won't look" in _consent_cancelled_message("en")


def test_amharic_consent_question_is_detected():
    assert _assistant_asked_for_appointment_consent(_consent_question("am"))


def test_english_consent_question_is_detected():
    assert _assistant_asked_for_appointment_consent(_consent_question("en"))


def test_unrelated_message_is_not_a_consent_question():
    assert not _assistant_asked_for_appointment_consent("Your test result is ready.")


@pytest.mark.parametrize(
    "message",
    [
        "Would you like me to check available doctors?",
        "Would you like me to search for available appointments?",
        "May I look for doctors in the appropriate department?",
        "Should I check appointment availability for you?",
        "Would you like help finding an available doctor?",
        "Would you like me to help explore appointment options?",
        "Would you like help arranging an appointment?",
        "Would you like help checking available appointment options?",
        "Would you like help exploring appointment options with a doctor "
        "to discuss these symptoms?",
        "If you are not experiencing an emergency and would like help "
        "exploring appointment options with a clinician to discuss "
        "these symptoms, please let me know.",
    ],
)
def test_alternative_english_appointment_consent_questions_are_detected(message):
    assert _assistant_asked_for_appointment_consent(message)


@pytest.mark.parametrize(
    "message",
    [
        "Your appointment is scheduled for Monday.",
        "Would you like to know what your appointment includes?",
        "I can explain how the appointment system works.",
        "Your doctor can discuss available treatment options.",
        "Would you like me to book an appointment for you?",
        "Your test result is ready.",
    ],
)
def test_non_search_questions_are_not_mistaken_for_search_consent(message):
    assert not _assistant_asked_for_appointment_consent(message)
