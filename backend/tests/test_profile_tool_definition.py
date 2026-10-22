from app.services.tool_definitions import HOSPITAL_TOOL_DEFINITIONS


def test_profile_tool_description_mentions_blood_type_and_missing_fields():
    profile_tool = next(
        tool for tool in HOSPITAL_TOOL_DEFINITIONS
        if tool["name"] == "getPatientProfile"
    )

    description = profile_tool["description"].casefold()

    assert "blood type" in description
    assert "allergies" in description
    assert "field is missing" in description
