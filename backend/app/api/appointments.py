"""Patient appointment booking API for the synthetic local demo."""

from datetime import date
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field

from app.core.auth import get_current_demo_staff, get_current_patient_id
from app.data.scheduling import DATA_SOURCE, DOCTORS, generate_synthetic_slots
from app.services.audit import record_audit_event
from app.services.hospital import hospital_service
from app.services.demo_scheduler import (
    DEMO_NOTICE,
    BookingConflictError,
    BookingNotFoundError,
    demo_scheduler,
)

router = APIRouter(tags=["Appointments"])


class BookingInput(BaseModel):
    """A patient-selected demo appointment slot."""

    model_config = ConfigDict(extra="forbid")

    doctorId: str = Field(min_length=1, max_length=64)
    date: date
    time: str = Field(min_length=5, max_length=5)
    purpose: str = Field(default="", max_length=200)


class RescheduleInput(BaseModel):
    """The replacement slot selected by the authenticated patient."""

    model_config = ConfigDict(extra="forbid")

    doctorId: str = Field(min_length=1, max_length=64)
    date: date
    time: str = Field(min_length=5, max_length=5)


def _require_future_date(value: date) -> str:
    if value < date.today():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Appointment date cannot be in the past.",
        )
    return value.isoformat()


def _handle_booking_value_error(exc: ValueError) -> None:
    """Translate known capacity conflicts into HTTP 409 responses."""
    message = str(exc)
    normalized = message.casefold()

    if any(word in normalized for word in ("full", "already have")):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=message,
        ) from exc

    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail=message,
    ) from exc


def _doctor_or_404(doctor_id: str) -> dict[str, Any]:
    doctor = next(
        (item for item in DOCTORS if item["id"] == doctor_id),
        None,
    )
    if doctor is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Doctor not found.",
        )
    return doctor


def _audit(
    patient_id: str,
    event: str,
    booking: dict[str, Any],
) -> None:
    """Record minimal booking metadata; do not log the appointment purpose."""
    record_audit_event(
        {
            "patientId": patient_id,
            "event": event,
            "details": {
                "bookingId": booking.get("bookingId"),
                "doctorId": booking.get("doctorId"),
                "date": booking.get("date"),
                "time": booking.get("time"),
                "dataSource": DATA_SOURCE,
            },
        }
    )


@router.get("/api/appointments/departments")
async def list_departments(
    _patient_id: str = Depends(get_current_patient_id),
) -> dict[str, Any]:
    departments = sorted({doctor["department"] for doctor in DOCTORS})
    return {
        "departments": departments,
        "dataSource": DATA_SOURCE,
        "dataNotice": DEMO_NOTICE,
    }


@router.get("/api/appointments/doctors")
async def list_doctors(
    department: str | None = Query(default=None, max_length=100),
    _patient_id: str = Depends(get_current_patient_id),
) -> dict[str, Any]:
    doctors = [
        {
            "id": doctor["id"],
            "name": doctor["name"],
            "department": doctor["department"],
            "specialties": doctor["specialties"],
            "location": doctor["location"],
        }
        for doctor in DOCTORS
        if (
            not department
            or doctor["department"].casefold() == department.strip().casefold()
        )
    ]

    return {
        "doctors": doctors,
        "dataSource": DATA_SOURCE,
        "dataNotice": DEMO_NOTICE,
    }


@router.get("/api/appointments/availability")
async def list_availability(
    doctorId: str = Query(min_length=1, max_length=64),
    startDate: date = Query(),
    days: int = Query(default=14, ge=1, le=30),
    _patient_id: str = Depends(get_current_patient_id),
) -> dict[str, Any]:
    doctor = _doctor_or_404(doctorId)
    start = _require_future_date(startDate)

    slots = generate_synthetic_slots(
        doctor_id=doctorId,
        start_date=date.fromisoformat(start),
        days=days,
    )

    for slot in slots:
        capacity = demo_scheduler.get_slot_status(
            doctorId,
            slot["date"],
            slot["time"],
        )
        slot.update(
            {
                "doctorName": doctor["name"],
                "location": doctor["location"],
                "slotCapacity": capacity["slotCapacity"],
                "slotBookedCount": capacity["slotBookedCount"],
                "slotRemainingCapacity": capacity["slotRemainingCapacity"],
                "dailyCapacity": capacity["dailyCapacity"],
                "dailyBookedCount": capacity["dailyBookedCount"],
                "dailyRemainingCapacity": capacity["dailyRemainingCapacity"],
                "available": capacity["available"],
                "dataNotice": DEMO_NOTICE,
            }
        )

    return {
        "slots": slots,
        "dataSource": DATA_SOURCE,
        "dataNotice": DEMO_NOTICE,
        "notice": "These are fictional demo slots, not live hospital availability.",
    }


@router.post("/api/appointments/book", status_code=status.HTTP_201_CREATED)
async def book_appointment(
    payload: BookingInput,
    patient_id: str = Depends(get_current_patient_id),
) -> dict[str, Any]:
    _doctor_or_404(payload.doctorId)
    appointment_date = _require_future_date(payload.date)

    try:
        booking = demo_scheduler.book_appointment(
            patient_id=patient_id,
            doctor_id=payload.doctorId,
            appointment_date=appointment_date,
            appointment_time=payload.time,
            purpose=payload.purpose,
        )
    except BookingConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        _handle_booking_value_error(exc)

    _audit(patient_id, "demo_appointment_booked", booking)

    return {
        "booking": booking,
        "dataSource": DATA_SOURCE,
        "dataNotice": DEMO_NOTICE,
    }


@router.get("/api/patient/appointments")
async def list_patient_appointments(
    patient_id: str = Depends(get_current_patient_id),
) -> dict[str, Any]:
    appointments = hospital_service.get_patient_appointments(
        patient_id,
        include_inactive=True,
        scheduler=demo_scheduler,
    )
    return {
        "appointments": appointments,
        "dataSource": DATA_SOURCE,
        "dataNotice": DEMO_NOTICE,
    }


@router.get("/api/patient/appointments/{booking_id}")
async def get_patient_appointment(
    booking_id: str,
    patient_id: str = Depends(get_current_patient_id),
) -> dict[str, Any]:
    appointments = hospital_service.get_patient_appointments(
        patient_id,
        include_inactive=True,
        scheduler=demo_scheduler,
    )

    booking = next(
        (
            item for item in appointments
            if item.get("bookingId") == booking_id
        ),
        None,
    )

    if booking is None:
        raise HTTPException(status_code=404, detail="Appointment not found.")

    return {
        "booking": booking,
        "dataSource": DATA_SOURCE,
        "dataNotice": DEMO_NOTICE,
    }


@router.post("/api/patient/appointments/{booking_id}/cancel")
async def cancel_patient_appointment(
    booking_id: str,
    patient_id: str = Depends(get_current_patient_id),
) -> dict[str, Any]:
    appointments = hospital_service.get_patient_appointments(
        patient_id,
        include_inactive=True,
        scheduler=demo_scheduler,
    )
    existing = next(
        (
            item for item in appointments
            if item.get("bookingId") == booking_id
        ),
        None,
    )

    if existing is None:
        raise HTTPException(status_code=404, detail="Appointment not found.")

    if existing.get("readOnly") is True:
        raise HTTPException(
            status_code=409,
            detail="This appointment was scheduled by hospital staff and cannot be cancelled by the patient.",
        )

    try:
        booking = demo_scheduler.cancel_appointment(patient_id, booking_id)
    except BookingNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Appointment not found.") from exc
    except BookingConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    _audit(patient_id, "demo_appointment_cancelled", booking)

    return {
        "booking": booking,
        "dataSource": DATA_SOURCE,
        "dataNotice": DEMO_NOTICE,
    }


@router.post("/api/patient/appointments/{booking_id}/reschedule")
async def reschedule_patient_appointment(
    booking_id: str,
    payload: RescheduleInput,
    patient_id: str = Depends(get_current_patient_id),
) -> dict[str, Any]:
    appointments = hospital_service.get_patient_appointments(
        patient_id,
        include_inactive=True,
        scheduler=demo_scheduler,
    )
    existing = next(
        (
            item for item in appointments
            if item.get("bookingId") == booking_id
        ),
        None,
    )

    if existing is None:
        raise HTTPException(status_code=404, detail="Appointment not found.")

    if existing.get("readOnly") is True:
        raise HTTPException(
            status_code=409,
            detail="This appointment was scheduled by hospital staff and cannot be rescheduled by the patient.",
        )

    _doctor_or_404(payload.doctorId)
    appointment_date = _require_future_date(payload.date)

    try:
        result = demo_scheduler.reschedule_appointment(
            patient_id=patient_id,
            booking_id=booking_id,
            doctor_id=payload.doctorId,
            appointment_date=appointment_date,
            appointment_time=payload.time,
        )
    except BookingNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Appointment not found.") from exc
    except BookingConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        _handle_booking_value_error(exc)

    _audit(patient_id, "demo_appointment_rescheduled", result["booking"])

    return {
        **result,
        "dataSource": DATA_SOURCE,
        "dataNotice": DEMO_NOTICE,
    }

class AttendanceInput(BaseModel):
    """Attendance outcome submitted by authorized demo staff."""

    model_config = ConfigDict(extra="forbid")

    outcome: Literal["attended", "missed"]


@router.get("/api/staff/appointments")
async def list_staff_appointments(
    _staff_id: str = Depends(get_current_demo_staff),
) -> dict[str, Any]:
    """List synthetic bookings for authenticated demo staff."""
    return {
        "appointments": demo_scheduler.get_all_bookings(),
        "dataSource": DATA_SOURCE,
        "dataNotice": DEMO_NOTICE,
    }


@router.post("/api/staff/appointments/{booking_id}/attendance")
async def record_staff_attendance(
    booking_id: str,
    payload: AttendanceInput,
    staff_id: str = Depends(get_current_demo_staff),
) -> dict[str, Any]:
    """Record an attendance outcome using staff-only authentication."""
    try:
        booking = demo_scheduler.record_attendance(
            booking_id=booking_id,
            outcome=payload.outcome,
            recorded_by=staff_id,
        )
    except BookingNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Appointment not found.") from exc
    except BookingConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    record_audit_event(
        {
            "patientId": booking.get("patientId"),
            "event": "demo_appointment_attendance_recorded",
            "details": {
                "bookingId": booking.get("bookingId"),
                "outcome": payload.outcome,
                "recordedBy": staff_id,
                "dataSource": DATA_SOURCE,
            },
        }
    )

    return {
        "booking": booking,
        "dataSource": DATA_SOURCE,
        "dataNotice": DEMO_NOTICE,
    }


