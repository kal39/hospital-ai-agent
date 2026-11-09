from datetime import date, timedelta

import pytest

from app.services.demo_scheduler import DemoScheduler, DEMO_SLOT_TIMES


def next_weekday() -> str:
    selected = date.today() + timedelta(days=1)
    while selected.weekday() >= 5:
        selected += timedelta(days=1)
    return selected.isoformat()


@pytest.fixture
def scheduler():
    return DemoScheduler()


def test_successful_booking_returns_demo_confirmation(scheduler):
    booking = scheduler.book_appointment(
        patient_id="patient-001",
        doctor_id="doctor-001",
        appointment_date=next_weekday(),
        appointment_time="09:00",
        purpose="Routine follow-up",
    )

    assert booking["status"] == "confirmed_demo"
    assert booking["doctorId"] == "doctor-001"
    assert booking["time"] == "09:00"
    assert booking["purpose"] == "Routine follow-up"
    assert booking["dataSource"] == "synthetic_demo"
    assert "patientId" not in booking
    assert "fictional" in booking["dataNotice"].lower()


def test_duplicate_booking_is_rejected(scheduler):
    appointment_date = next_weekday()
    arguments = {
        "patient_id": "patient-001",
        "doctor_id": "doctor-001",
        "appointment_date": appointment_date,
        "appointment_time": "09:00",
    }

    scheduler.book_appointment(**arguments)

    with pytest.raises(ValueError, match="already have a demo booking"):
        scheduler.book_appointment(**arguments)


def test_slot_capacity_is_reflected_in_status(scheduler):
    appointment_date = next_weekday()

    scheduler.book_appointment(
        "patient-001", "doctor-001", appointment_date, "09:00"
    )
    scheduler.book_appointment(
        "patient-002", "doctor-001", appointment_date, "09:00"
    )

    status = scheduler.get_slot_status(
        "doctor-001", appointment_date, "09:00"
    )

    assert status["slotBookedCount"] == 2
    assert status["slotRemainingCapacity"] == 0
    assert status["available"] is False


def test_daily_capacity_cannot_be_exceeded(scheduler):
    appointment_date = next_weekday()

    # Two different demo patients fill each of the four time slots.
    for appointment_time in DEMO_SLOT_TIMES:
        for patient_id in ("patient-001", "patient-002"):
            scheduler.book_appointment(
                patient_id=patient_id,
                doctor_id="doctor-001",
                appointment_date=appointment_date,
                appointment_time=appointment_time,
            )

    summary = scheduler.get_day_summary("doctor-001", appointment_date)

    assert summary["bookedCount"] == 8
    assert summary["remainingCapacity"] == 0

    with pytest.raises(ValueError, match="daily capacity is full"):
        scheduler.book_appointment(
            patient_id="patient-001",
            doctor_id="doctor-001",
            appointment_date=appointment_date,
            appointment_time="09:00",
        )


def test_patient_booking_lists_are_isolated(scheduler):
    appointment_date = next_weekday()

    scheduler.book_appointment(
        "patient-001", "doctor-001", appointment_date, "09:00"
    )
    scheduler.book_appointment(
        "patient-002", "doctor-001", appointment_date, "10:30"
    )

    patient_one_bookings = scheduler.get_patient_bookings("patient-001")
    patient_two_bookings = scheduler.get_patient_bookings("patient-002")

    assert len(patient_one_bookings) == 1
    assert len(patient_two_bookings) == 1
    assert patient_one_bookings[0]["time"] == "09:00"
    assert patient_two_bookings[0]["time"] == "10:30"

    for booking in patient_one_bookings + patient_two_bookings:
        assert "patientId" not in booking


@pytest.mark.parametrize(
    "patient_id",
    ["", "   ", "patient-999"],
)
def test_invalid_patient_is_rejected(scheduler, patient_id):
    with pytest.raises(ValueError):
        scheduler.book_appointment(
            patient_id=patient_id,
            doctor_id="doctor-001",
            appointment_date=next_weekday(),
            appointment_time="09:00",
        )


def test_past_appointment_date_is_rejected(scheduler):
    yesterday = (date.today() - timedelta(days=1)).isoformat()

    with pytest.raises(ValueError, match="past"):
        scheduler.book_appointment(
            "patient-001", "doctor-001", yesterday, "09:00"
        )


def test_invalid_time_is_rejected(scheduler):
    with pytest.raises(ValueError, match="valid demo appointment time"):
        scheduler.book_appointment(
            "patient-001", "doctor-001", next_weekday(), "11:00"
        )


def test_unknown_doctor_is_rejected(scheduler):
    with pytest.raises(ValueError, match="Doctor not found"):
        scheduler.book_appointment(
            "patient-001", "doctor-999", next_weekday(), "09:00"
        )
