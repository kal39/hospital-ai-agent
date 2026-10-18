
import pytest

from app.services.hospital import hospital_service
from app.services.tool_executor import execute_hospital_tool


def test_get_patient_profile():
    result = execute_hospital_tool("getPatientProfile", "patient-001")

    assert result["id"] == "patient-001"
    assert result["firstName"] == "Abebe"


def test_get_latest_lab_results():
    result = execute_hospital_tool("getLatestLabResults", "patient-001")

    assert len(result) == 3
    assert all(item["date"] == "2026-10-01" for item in result)
    assert all("dataNotice" in item for item in result)


def test_compare_lab_results():
    result = execute_hospital_tool("compareLabResults", "patient-001")

    assert len(result) == 3
    assert all(
        "testName" in item and "change" in item
        for item in result
    )


def test_get_medications():
    result = execute_hospital_tool("getMedications", "patient-001")

    assert len(result) == 1
    assert result[0]["name"] == "Amlodipine"


def test_get_medical_history():
    result = execute_hospital_tool("getMedicalHistory", "patient-001")

    assert len(result) == 3


def test_each_patient_receives_their_own_profile():
    patient_001 = execute_hospital_tool(
        "getPatientProfile",
        "patient-001",
    )
    patient_002 = execute_hospital_tool(
        "getPatientProfile",
        "patient-002",
    )

    assert patient_001["id"] == "patient-001"
    assert patient_002["id"] == "patient-002"
    assert patient_001["id"] != patient_002["id"]


def test_lab_results_are_scoped_to_the_requested_patient():
    patient_001_results = execute_hospital_tool(
        "getLatestLabResults",
        "patient-001",
    )
    patient_002_results = execute_hospital_tool(
        "getLatestLabResults",
        "patient-002",
    )

    expected_001 = hospital_service.get_latest_lab_results(
        "patient-001"
    )
    expected_002 = hospital_service.get_latest_lab_results(
        "patient-002"
    )

    assert patient_001_results == expected_001
    assert patient_002_results == expected_002

    # Both results must retain the synthetic-data warning.
    for result in patient_001_results + patient_002_results:
        assert result["dataNotice"]
        assert result["dataSource"]


@pytest.mark.parametrize("patient_id", ["", "   "])
def test_missing_patient_identity_is_rejected(patient_id):
    with pytest.raises(
        ValueError,
        match="Authenticated patient identity is required",
    ):
        execute_hospital_tool("getPatientProfile", patient_id)


def test_unknown_tool_is_rejected():
    with pytest.raises(
        ValueError,
        match="Unauthorized or unknown hospital tool",
    ):
        execute_hospital_tool(
            "deletePatientRecord",
            "patient-001",
        )


def test_unknown_patient_profile_is_rejected():
    with pytest.raises(
        ValueError,
        match="Patient record not found",
    ):
        execute_hospital_tool(
            "getPatientProfile",
            "patient-999",
        )


def test_unknown_patient_cannot_retrieve_lab_results():
    with pytest.raises(
        ValueError,
        match="Patient record not found",
    ):
        execute_hospital_tool(
            "getLatestLabResults",
            "patient-999",
        )


@pytest.mark.parametrize(
    "injected_arguments",
    [
        {"patient_id": "patient-002"},
        {"patientId": "patient-002"},
    ],
)
def test_model_cannot_override_patient_identity_in_tool_arguments(
    injected_arguments,
):
    # The trusted patient identity is supplied separately.
    # A model-supplied identity must be rejected, not used.
    with pytest.raises(
        ValueError,
        match="Unexpected arguments",
    ):
        execute_hospital_tool(
            "getLatestLabResults",
            "patient-001",
            arguments=injected_arguments,
        )
