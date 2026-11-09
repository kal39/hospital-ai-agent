from datetime import date, timedelta

import pytest

from app.services.hospital import HospitalService, demo_scheduler
from app.services.tool_executor import execute_hospital_tool


def future_weekday(days_ahead: int) -> str:
    """Return a future weekday suitable for demo appointment booking."""
    selected = date.today() + timedelta(days=days_ahead)

    while selected.weekday() >= 5:
        selected += timedelta(days=1)

    return selected.isoformat()


def create_booking(
    patient_id: str,
    days_ahead: int,
    doctor_id: str = "doctor-001",
    appointment_time: str = "09:00",
):
    """Create a booking through the same scheduler used by the booking API."""
    return demo_scheduler.book_appointment(
        patient_id=patient_id,
        doctor_id=doctor_id,
        appointment_date=future_weekday(days_ahead),
        appointment_time=appointment_time,
        purpose="Automated appointment integration test",
    )


def test_upcoming_appointments_include_shared_scheduler_booking():
    booking = create_booking("patient-001", 40)

    service = HospitalService()
    appointments = service.get_upcoming_appointments("patient-001")

    matching = [
        appointment
        for appointment in appointments
        if appointment["bookingId"] == booking["bookingId"]
    ]

    assert len(matching) == 1
    assert matching[0]["id"] == booking["bookingId"]
    assert matching[0]["status"] == "confirmed_demo"
    assert matching[0]["date"] >= date.today().isoformat()


def test_patient_appointments_are_isolated():
    booking_one = create_booking(
        "patient-001",
        45,
        doctor_id="doctor-001",
        appointment_time="09:00",
    )
    booking_two = create_booking(
        "patient-002",
        46,
        doctor_id="doctor-002",
        appointment_time="10:30",
    )

    patient_one = execute_hospital_tool(
        "getUpcomingAppointments",
        "patient-001",
    )
    patient_two = execute_hospital_tool(
        "getUpcomingAppointments",
        "patient-002",
    )

    patient_one_ids = {appointment["id"] for appointment in patient_one}
    patient_two_ids = {appointment["id"] for appointment in patient_two}

    assert booking_one["bookingId"] in patient_one_ids
    assert booking_two["bookingId"] in patient_two_ids
    assert patient_one_ids.isdisjoint(patient_two_ids)


def test_preparation_context_contains_expected_sections():
    create_booking("patient-001", 50)

    context = execute_hospital_tool(
        "getAppointmentPreparationContext",
        "patient-001",
    )

    assert context["appointments"]
    assert context["latestLabResults"]
    assert context["medications"]
    assert context["recentMedicalHistory"]
    assert "allergies" in context["profile"]


def test_preparation_context_uses_shared_scheduler_booking():
    booking = create_booking("patient-001", 55)

    context = execute_hospital_tool(
        "getAppointmentPreparationContext",
        "patient-001",
    )

    booking_ids = {
        appointment["bookingId"]
        for appointment in context["appointments"]
    }

    assert booking["bookingId"] in booking_ids


def test_preparation_context_does_not_include_other_patient_records():
    other_patient_booking = create_booking(
        "patient-002",
        60,
        doctor_id="doctor-002",
        appointment_time="13:00",
    )
    create_booking("patient-001", 61)

    context = execute_hospital_tool(
        "getAppointmentPreparationContext",
        "patient-001",
    )

    booking_ids = {
        appointment["bookingId"]
        for appointment in context["appointments"]
    }

    assert other_patient_booking["bookingId"] not in booking_ids
    assert all(
        medication["id"] != "med-002"
        for medication in context["medications"]
    )


def test_cancelled_booking_is_not_returned_as_upcoming():
    booking = create_booking("patient-001", 65)

    demo_scheduler.cancel_appointment(
        "patient-001",
        booking["bookingId"],
    )

    appointments = HospitalService().get_upcoming_appointments("patient-001")
    booking_ids = {
        appointment["bookingId"]
        for appointment in appointments
    }

    assert booking["bookingId"] not in booking_ids


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