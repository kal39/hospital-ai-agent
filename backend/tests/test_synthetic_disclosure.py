import pytest

from app.services.agent import (
    _add_synthetic_data_disclosure,
    _uses_synthetic_record_tool,
)


@pytest.mark.parametrize(
    "tool_name",
    [
        "getPatientProfile",
        "getLatestLabResults",
        "getMedications",
        "getMedicalHistory",
        "getAvailableAppointmentSlots",
        "getQueueEstimate",
    ],
)
def test_synthetic_record_tools_require_disclosure(tool_name):
    assert _uses_synthetic_record_tool([tool_name]) is True


def test_unrelated_tool_does_not_trigger_synthetic_disclosure():
    assert _uses_synthetic_record_tool(["searchHospitalFaq"]) is False


def test_invalid_tool_collection_does_not_trigger_disclosure():
    assert _uses_synthetic_record_tool(None) is False


def test_english_disclosure_is_added_to_response():
    result = _add_synthetic_data_disclosure(
        "Your latest results are within the listed reference ranges.",
        "en",
    )

    assert "Synthetic-data notice:" in result
    assert "fictional demonstration records" in result
    assert "live hospital system" in result
    assert "Your latest results" in result


def test_amharic_disclosure_is_added_to_response():
    result = _add_synthetic_data_disclosure(
        "ውጤቶችዎ እነሆ።",
        "am",
    )

    assert "ማሳሰቢያ" in result
    assert "ሰው ሰራሽ የሙከራ" in result
    assert "ውጤቶችዎ እነሆ።" in result


def test_empty_response_still_gets_disclosure():
    result = _add_synthetic_data_disclosure("", "en")

    assert "Synthetic-data notice:" in result
    assert "fictional demonstration records" in result


def test_whitespace_response_still_gets_disclosure():
    result = _add_synthetic_data_disclosure("   ", "en")

    assert "Synthetic-data notice:" in result


def test_complete_english_disclosure_is_not_duplicated():
    notice = (
        "Synthetic-data notice: The following information comes from "
        "fictional demonstration records, not verified records from "
        "a live hospital system. Verify it with your healthcare "
        "professional before relying on it for clinical decisions."
    )
    response = f"{notice}\n\nHere are your results."

    assert _add_synthetic_data_disclosure(response, "en") == response


def test_partial_synthetic_mention_does_not_suppress_disclosure():
    response = "These results use synthetic development data."

    result = _add_synthetic_data_disclosure(response, "en")

    assert result.startswith("Synthetic-data notice:")


def test_duplicate_disclaimers_are_replaced():
    response = (
        "Synthetic-data notice: Fictional demonstration records.\\n\\n"
        "Disclaimer: Not verified live hospital data.\\n\\n"
        "Your fasting glucose is 112 mg/dL."
    )

    result = _add_synthetic_data_disclosure(response, "en")

    assert result.count("Synthetic-data notice:") == 1
    assert "Disclaimer:" not in result
    assert "Your fasting glucose is 112 mg/dL." in result


def test_malformed_amharic_disclaimer_is_removed():
    response = (
        "ማሳሰቢያ፦ ይህ የሙከራ መረጃ ነው።\\n\\n"
        "ከপ্রেডተ (synthetic demo) የተገኘ መረጃ ነው።\\n\\n"
        "የሄሞግሎቢን ውጤትዎ 13.8 g/dL ነው።"
    )

    result = _add_synthetic_data_disclosure(response, "am")

    assert result.count("ማሳሰቢያ፦") == 1
    assert "synthetic demo" not in result.casefold()
    assert "የሄሞግሎቢን ውጤትዎ 13.8 g/dL ነው።" in result
