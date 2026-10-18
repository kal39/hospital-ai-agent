
from app.services.agent import (
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
