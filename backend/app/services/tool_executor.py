
"""Execute approved hospital tools with backend-enforced authorization."""

from typing import Any

from app.services.hospital import hospital_service
from app.services.tool_definitions import HOSPITAL_TOOL_DEFINITIONS


APPROVED_TOOLS = {
    tool["name"] for tool in HOSPITAL_TOOL_DEFINITIONS
}

APPOINTMENT_DISCOVERY_TOOLS = {
    "findAppropriateDoctors",
    "getAvailableAppointmentSlots",
    "getQueueEstimate",
}

TOOL_ARGUMENTS = {
    "getLatestLabResults": set(),
    "compareLabResults": set(),
    "getMedications": set(),
    "getMedicalHistory": set(),
    "getPatientProfile": set(),
    "getUpcomingAppointments": set(),
    "getAppointmentPreparationContext": set(),
    "findAppropriateDoctors": {"department"},
    "getAvailableAppointmentSlots": {
        "doctorId",
        "department",
        "startDate",
        "days",
    },
    "getQueueEstimate": {
        "doctorId",
        "appointmentDate",
    },
}


def _validate_arguments(
    tool_name: str,
    arguments: dict[str, Any],
) -> None:
    """Reject unexpected or incorrectly typed tool arguments."""
    if not isinstance(arguments, dict):
        raise ValueError("Tool arguments must be an object.")

    allowed = TOOL_ARGUMENTS.get(tool_name, set())
    unexpected = set(arguments) - allowed

    if unexpected:
        raise ValueError(
            f"Unexpected arguments for {tool_name}: "
            f"{', '.join(sorted(unexpected))}"
        )

    for name, value in arguments.items():
        if name == "days":
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or not 1 <= value <= 30
            ):
                raise ValueError(
                    "The days argument must be an integer from 1 to 30."
                )
            continue

        if not isinstance(value, str) or len(value) > 100:
            raise ValueError(
                f"Invalid value for argument: {name}"
            )

    if tool_name == "getQueueEstimate":
        doctor_id = arguments.get("doctorId", "")
        if not doctor_id.strip():
            raise ValueError("A doctorId is required.")


def execute_hospital_tool(
    tool_name: str,
    patient_id: str,
    arguments: dict[str, Any] | None = None,
    *,
    allow_appointment_discovery: bool = False,
) -> Any:
    """Execute an approved tool for the authenticated patient.

    Appointment discovery is denied unless the trusted caller explicitly
    supplies permission after the conversation's consent check.
    """
    if not patient_id or not patient_id.strip():
        raise ValueError(
            "Authenticated patient identity is required."
        )

    if tool_name not in APPROVED_TOOLS:
        raise ValueError(
            f"Unauthorized or unknown hospital tool: {tool_name}"
        )

    # Defense in depth: enforce consent outside the LLM prompt.
    if (
        tool_name in APPOINTMENT_DISCOVERY_TOOLS
        and allow_appointment_discovery is not True
    ):
        raise PermissionError(
            "Explicit consent is required before appointment discovery."
        )

    if not hospital_service.get_patient_profile(patient_id):
        raise ValueError("Patient record not found.")

    validated_arguments = arguments or {}
    _validate_arguments(tool_name, validated_arguments)

    if tool_name == "getLatestLabResults":
        return hospital_service.get_latest_lab_results(patient_id)

    if tool_name == "compareLabResults":
        return hospital_service.compare_lab_results(patient_id)

    if tool_name == "getMedications":
        return hospital_service.get_medications(patient_id)

    if tool_name == "getMedicalHistory":
        return hospital_service.get_medical_history(patient_id)

    if tool_name == "getPatientProfile":
        return hospital_service.get_patient_profile(patient_id)

    if tool_name == "getUpcomingAppointments":
        return hospital_service.get_upcoming_appointments(patient_id)

    if tool_name == "getAppointmentPreparationContext":
        return hospital_service.get_appointment_preparation_context(
            patient_id
        )

    if tool_name == "findAppropriateDoctors":
        return hospital_service.find_appropriate_doctors(
            patient_id,
            department=validated_arguments.get("department", ""),
        )

    if tool_name == "getAvailableAppointmentSlots":
        return hospital_service.get_available_appointment_slots(
            patient_id,
            doctor_id=validated_arguments.get("doctorId", ""),
            department=validated_arguments.get("department", ""),
            start_date=validated_arguments.get("startDate", ""),
            days=validated_arguments.get("days", 14),
        )

    if tool_name == "getQueueEstimate":
        return hospital_service.get_queue_estimate(
            patient_id,
            doctor_id=validated_arguments["doctorId"],
            appointment_date=validated_arguments.get(
                "appointmentDate", ""
            ),
        )

    raise ValueError(
        f"Unauthorized or unknown hospital tool: {tool_name}"
    )
