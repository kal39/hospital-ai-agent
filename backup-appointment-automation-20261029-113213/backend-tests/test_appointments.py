
from datetime import date

import pytest

from app.services.hospital import HospitalService
from app.services.tool_executor import execute_hospital_tool


def test_upcoming_appointments_are_returned_for_patient():
    service = HospitalService()

    appointments = service.get_upcoming_appointments("patient-001")

    assert appointments
    assert all(
        appointment["date"] >= date.today().isoformat()
        for appointment in appointments
    )
    assert all(
        appointment["status"] in {"scheduled", "confirmed"}
        for appointment in appointments
    )


def test_patient_appointments_are_isolated():
    patient_one = execute_hospital_tool(
        "getUpcomingAppointments",
        "patient-001",
    )
    patient_two = execute_hospital_tool(
        "getUpcomingAppointments",
        "patient-002",
    )

    assert patient_one
    assert patient_two
    assert {
        appointment["id"] for appointment in patient_one
    }.isdisjoint({
        appointment["id"] for appointment in patient_two
    })


def test_preparation_context_contains_expected_sections():
    context = execute_hospital_tool(
        "getAppointmentPreparationContext",
        "patient-001",
    )

    assert context["appointments"]
    assert context["latestLabResults"]
    assert context["medications"]
    assert context["recentMedicalHistory"]
    assert "allergies" in context["profile"]


def test_preparation_context_does_not_include_other_patient_records():
    context = execute_hospital_tool(
        "getAppointmentPreparationContext",
        "patient-001",
    )

    assert all(
        appointment["id"] != "appt-002"
        for appointment in context["appointments"]
    )
    assert all(
        medication["id"] != "med-002"
        for medication in context["medications"]
    )


def test_unknown_patient_cannot_access_preparation_context():
    with pytest.raises(ValueError, match="Patient record not found"):
        execute_hospital_tool(
            "getAppointmentPreparationContext",
            "unknown-patient",
        )


def test_unapproved_tool_is_rejected():
    with pytest.raises(ValueError, match="Unauthorized or unknown"):
        execute_hospital_tool(
            "deletePatientRecord",
            "patient-001",
        )
