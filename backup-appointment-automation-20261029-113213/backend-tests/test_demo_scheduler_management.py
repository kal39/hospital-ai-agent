from datetime import date, timedelta

import pytest

from app.services.demo_scheduler import (
    BookingConflictError,
    BookingNotFoundError,
    DemoScheduler,
)


def next_weekday(offset=1):
    selected = date.today() + timedelta(days=offset)
    while selected.weekday() >= 5:
        selected += timedelta(days=1)
    return selected.isoformat()


@pytest.fixture
def scheduler():
    instance = DemoScheduler()
    yield instance
    instance._connection.close()


def make_booking(scheduler, patient="patient-001", time="09:00"):
    return scheduler.book_appointment(
        patient_id=patient,
        doctor_id="doctor-001",
        appointment_date=next_weekday(),
        appointment_time=time,
        purpose="Routine follow-up",
    )


def test_cancelled_booking_is_removed_from_active_list(scheduler):
    booking = make_booking(scheduler)

    cancelled = scheduler.cancel_appointment(
        "patient-001", booking["bookingId"]
    )

    assert cancelled["status"] == "cancelled_demo"
    assert scheduler.get_patient_bookings("patient-001") == []
    assert len(
        scheduler.get_patient_bookings(
            "patient-001", include_inactive=True
        )
    ) == 1


def test_cancellation_releases_slot_capacity(scheduler):
    booking = make_booking(scheduler)
    appointment_date = booking["date"]

    scheduler.book_appointment(
        "patient-002",
        "doctor-001",
        appointment_date,
        "09:00",
    )

    before = scheduler.get_slot_status(
        "doctor-001", appointment_date, "09:00"
    )
    assert before["slotBookedCount"] == 2
    assert before["available"] is False

    scheduler.cancel_appointment(
        "patient-001", booking["bookingId"]
    )

    after = scheduler.get_slot_status(
        "doctor-001", appointment_date, "09:00"
    )
    assert after["slotBookedCount"] == 1
    assert after["slotRemainingCapacity"] == 1
    assert after["available"] is True


def test_cancelled_booking_cannot_be_cancelled_again(scheduler):
    booking = make_booking(scheduler)
    scheduler.cancel_appointment("patient-001", booking["bookingId"])

    with pytest.raises(BookingConflictError, match="active demo appointment"):
        scheduler.cancel_appointment("patient-001", booking["bookingId"])


def test_patient_cannot_cancel_another_patients_booking(scheduler):
    booking = make_booking(scheduler)

    with pytest.raises(BookingNotFoundError):
        scheduler.cancel_appointment("patient-002", booking["bookingId"])

    assert len(scheduler.get_patient_bookings("patient-001")) == 1


def test_patient_cannot_view_another_patients_booking(scheduler):
    booking = make_booking(scheduler)

    with pytest.raises(BookingNotFoundError):
        scheduler.get_patient_booking("patient-002", booking["bookingId"])


def test_successful_reschedule_replaces_old_booking(scheduler):
    old_booking = make_booking(scheduler)

    result = scheduler.reschedule_appointment(
        patient_id="patient-001",
        booking_id=old_booking["bookingId"],
        doctor_id="doctor-001",
        appointment_date=next_weekday(2),
        appointment_time="10:30",
    )

    new_booking = result["booking"]
    assert new_booking["status"] == "confirmed_demo"
    assert new_booking["date"] == next_weekday(2)
    assert new_booking["time"] == "10:30"
    assert new_booking["bookingId"] != old_booking["bookingId"]

    old_history = scheduler.get_patient_booking(
        "patient-001", old_booking["bookingId"]
    )
    assert old_history["status"] == "rescheduled_demo"

    active = scheduler.get_patient_bookings("patient-001")
    assert len(active) == 1
    assert active[0]["bookingId"] == new_booking["bookingId"]


def test_failed_reschedule_preserves_original_booking(scheduler, monkeypatch):
    from app.data import patients

    # Add a temporary third patient so the target slot can be filled
    # without triggering the duplicate-booking validation first.
    monkeypatch.setitem(
        patients.PATIENTS,
        "patient-test-003",
        {"id": "patient-test-003", "firstName": "Test", "lastName": "Patient"},
    )

    appointment_date = next_weekday()
    original = scheduler.book_appointment(
        "patient-001", "doctor-001", appointment_date, "09:00"
    )

    target_date = next_weekday(2)
    scheduler.book_appointment(
        "patient-002", "doctor-001", target_date, "10:30"
    )
    scheduler.book_appointment(
        "patient-test-003", "doctor-001", target_date, "10:30"
    )

    with pytest.raises(BookingConflictError, match="slot is full"):
        scheduler.reschedule_appointment(
            patient_id="patient-001",
            booking_id=original["bookingId"],
            doctor_id="doctor-001",
            appointment_date=target_date,
            appointment_time="10:30",
        )

    original_after = scheduler.get_patient_booking(
        "patient-001", original["bookingId"]
    )
    assert original_after["status"] == "confirmed_demo"
    assert len(scheduler.get_patient_bookings("patient-001")) == 1

def test_rescheduling_to_same_slot_is_rejected(scheduler):
    booking = make_booking(scheduler)

    with pytest.raises(BookingConflictError, match="different"):
        scheduler.reschedule_appointment(
            patient_id="patient-001",
            booking_id=booking["bookingId"],
            doctor_id="doctor-001",
            appointment_date=booking["date"],
            appointment_time=booking["time"],
        )

    assert len(scheduler.get_patient_bookings("patient-001")) == 1


def test_booking_persists_across_scheduler_instances(tmp_path):
    database = str(tmp_path / "appointments.sqlite3")
    first = DemoScheduler(db_path=database)

    try:
        booking = first.book_appointment(
            "patient-001",
            "doctor-001",
            next_weekday(),
            "09:00",
            "Persistence test",
        )
    finally:
        first._connection.close()

    second = DemoScheduler(db_path=database)
    try:
        bookings = second.get_patient_bookings("patient-001")
        assert len(bookings) == 1
        assert bookings[0]["bookingId"] == booking["bookingId"]
        assert bookings[0]["purpose"] == "Persistence test"
    finally:
        second._connection.close()
