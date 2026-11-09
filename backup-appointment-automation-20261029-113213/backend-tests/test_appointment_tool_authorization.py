
import pytest

from app.services.tool_executor import execute_hospital_tool


APPOINTMENT_TOOLS = [
    (
        "findAppropriateDoctors",
        {"department": "General Medicine"},
    ),
    (
        "getAvailableAppointmentSlots",
        {
            "doctorId": "doctor-001",
            "department": "General Medicine",
            "days": 7,
        },
    ),
    (
        "getQueueEstimate",
        {"doctorId": "doctor-001"},
    ),
]


@pytest.mark.parametrize(
    ("tool_name", "arguments"),
    APPOINTMENT_TOOLS,
)
def test_appointment_discovery_denied_without_consent(
    tool_name,
    arguments,
):
    with pytest.raises(
        PermissionError,
        match="Explicit consent is required",
    ):
        execute_hospital_tool(
            tool_name=tool_name,
            patient_id="patient-001",
            arguments=arguments,
        )


@pytest.mark.parametrize(
    ("tool_name", "arguments"),
    APPOINTMENT_TOOLS,
)
def test_appointment_discovery_allowed_with_permission(
    tool_name,
    arguments,
):
    result = execute_hospital_tool(
        tool_name=tool_name,
        patient_id="patient-001",
        arguments=arguments,
        allow_appointment_discovery=True,
    )

    assert isinstance(result, dict)
    assert result["dataSource"] == "synthetic_demo"


def test_booking_is_not_an_approved_tool():
    with pytest.raises(
        ValueError,
        match="Unauthorized or unknown hospital tool",
    ):
        execute_hospital_tool(
            tool_name="bookAppointment",
            patient_id="patient-001",
            arguments={"doctorId": "doctor-001"},
            allow_appointment_discovery=True,
        )
