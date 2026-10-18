"""In-memory appointment scheduler for the synthetic local prototype.

All records are fictional. This is not a production booking system.
Bookings reset when the process restarts. Replace this implementation
with an authorized, transaction-safe hospital scheduling API in production.
"""

from datetime import date
from threading import RLock
from typing import Any
from uuid import uuid4

from app.data.patients import PATIENTS
from app.data.scheduling import DATA_SOURCE, DOCTORS


DEMO_SLOT_TIMES = ("09:00", "10:30", "13:00", "14:30")
SLOT_CAPACITY = 2
DAILY_CAPACITY_PER_DOCTOR = len(DEMO_SLOT_TIMES) * SLOT_CAPACITY

DEMO_QUEUE_PEOPLE_AHEAD = 3
DEMO_MINUTES_PER_PATIENT = 15

DEMO_NOTICE = (
    "SYNTHETIC DEMONSTRATION DATA: This booking and availability "
    "information is fictional local prototype data, not a live hospital "
    "schedule. No real hospital appointment has been created."
)


class DemoScheduler:
    """Thread-safe, in-memory scheduler for local demonstration only."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._bookings: list[dict[str, Any]] = []

    @staticmethod
    def _doctor(doctor_id: str) -> dict[str, Any]:
        doctor = next(
            (item for item in DOCTORS if item["id"] == doctor_id),
            None,
        )
        if doctor is None:
            raise ValueError("Doctor not found.")
        return doctor

    @staticmethod
    def _validate_patient(patient_id: str) -> None:
        if not patient_id or not patient_id.strip():
            raise ValueError("Authenticated patient identity is required.")
        if patient_id not in PATIENTS:
            raise ValueError("Patient record not found.")

    @staticmethod
    def _validate_date(appointment_date: str) -> date:
        try:
            selected_date = date.fromisoformat(appointment_date)
        except (TypeError, ValueError) as error:
            raise ValueError(
                "appointmentDate must use YYYY-MM-DD format."
            ) from error

        if selected_date < date.today():
            raise ValueError("Appointments cannot be booked in the past.")

        if selected_date.weekday() >= 5:
            raise ValueError("Demo appointments are available on weekdays only.")

        return selected_date

    @staticmethod
    def _validate_time(appointment_time: str) -> None:
        if appointment_time not in DEMO_SLOT_TIMES:
            raise ValueError("This is not a valid demo appointment time.")

    def _active_bookings_for_day(
        self,
        doctor_id: str,
        appointment_date: str,
    ) -> list[dict[str, Any]]:
        return [
            booking
            for booking in self._bookings
            if booking["doctorId"] == doctor_id
            and booking["date"] == appointment_date
            and booking["status"] == "confirmed_demo"
        ]

    def _active_bookings_for_slot(
        self,
        doctor_id: str,
        appointment_date: str,
        appointment_time: str,
    ) -> list[dict[str, Any]]:
        return [
            booking
            for booking in self._active_bookings_for_day(
                doctor_id,
                appointment_date,
            )
            if booking["time"] == appointment_time
        ]

    def get_slot_status(
        self,
        doctor_id: str,
        appointment_date: str,
        appointment_time: str,
    ) -> dict[str, Any]:
        """Return aggregate capacity without revealing other patients."""
        self._doctor(doctor_id)
        self._validate_date(appointment_date)
        self._validate_time(appointment_time)

        with self._lock:
            day_bookings = self._active_bookings_for_day(
                doctor_id,
                appointment_date,
            )
            slot_bookings = self._active_bookings_for_slot(
                doctor_id,
                appointment_date,
                appointment_time,
            )

            return {
                "doctorId": doctor_id,
                "date": appointment_date,
                "time": appointment_time,
                "slotCapacity": SLOT_CAPACITY,
                "slotBookedCount": len(slot_bookings),
                "slotRemainingCapacity": SLOT_CAPACITY - len(slot_bookings),
                "dailyCapacity": DAILY_CAPACITY_PER_DOCTOR,
                "dailyBookedCount": len(day_bookings),
                "dailyRemainingCapacity": (
                    DAILY_CAPACITY_PER_DOCTOR - len(day_bookings)
                ),
                "available": len(slot_bookings) < SLOT_CAPACITY,
                "dataSource": DATA_SOURCE,
                "dataNotice": DEMO_NOTICE,
            }

    def get_day_summary(
        self,
        doctor_id: str,
        appointment_date: str,
    ) -> dict[str, Any]:
        """Return a doctor's aggregate bookings and synthetic queue estimate."""
        doctor = self._doctor(doctor_id)
        selected_date = self._validate_date(appointment_date)

        with self._lock:
            day_bookings = self._active_bookings_for_day(
                doctor_id,
                selected_date.isoformat(),
            )
            booked_count = len(day_bookings)

        # This is illustrative queue data, not a live waiting-room count.
        people_ahead = (
            DEMO_QUEUE_PEOPLE_AHEAD
            if selected_date.weekday() < 5
            else 0
        )

        return {
            "doctorId": doctor_id,
            "doctorName": doctor["name"],
            "date": selected_date.isoformat(),
            "bookedCount": booked_count,
            "dailyCapacity": DAILY_CAPACITY_PER_DOCTOR,
            "remainingCapacity": DAILY_CAPACITY_PER_DOCTOR - booked_count,
            "illustrativeQueueCount": people_ahead,
            "illustrativeWaitMinutes": (
                people_ahead * DEMO_MINUTES_PER_PATIENT
            ),
            "queueNotice": (
                "The queue count and wait estimate are fictional examples. "
                "They are not the current hospital waiting queue."
            ),
            "dataSource": DATA_SOURCE,
            "dataNotice": DEMO_NOTICE,
        }

    def book_appointment(
        self,
        patient_id: str,
        doctor_id: str,
        appointment_date: str,
        appointment_time: str,
        purpose: str = "",
    ) -> dict[str, Any]:
        """Create a demo booking after the caller verifies explicit consent."""
        self._validate_patient(patient_id)
        doctor = self._doctor(doctor_id)
        selected_date = self._validate_date(appointment_date)
        self._validate_time(appointment_time)

        normalized_purpose = purpose.strip()
        if len(normalized_purpose) > 200:
            raise ValueError("Appointment purpose must be 200 characters or fewer.")

        with self._lock:
            day_bookings = self._active_bookings_for_day(
                doctor_id,
                selected_date.isoformat(),
            )
            if len(day_bookings) >= DAILY_CAPACITY_PER_DOCTOR:
                raise ValueError("This doctor's demo daily capacity is full.")

            for booking in self._bookings:
                if (
                    booking["patientId"] == patient_id
                    and booking["doctorId"] == doctor_id
                    and booking["date"] == selected_date.isoformat()
                    and booking["time"] == appointment_time
                    and booking["status"] == "confirmed_demo"
                ):
                    raise ValueError(
                        "You already have a demo booking for this doctor, "
                        "date, and time."
                    )

            slot_bookings = self._active_bookings_for_slot(
                doctor_id,
                selected_date.isoformat(),
                appointment_time,
            )
            if len(slot_bookings) >= SLOT_CAPACITY:
                raise ValueError("This demo time slot is full.")

            booking = {
                "bookingId": f"demo-{uuid4().hex[:12]}",
                "patientId": patient_id,
                "doctorId": doctor_id,
                "doctorName": doctor["name"],
                "department": doctor["department"],
                "location": doctor["location"],
                "date": selected_date.isoformat(),
                "time": appointment_time,
                "purpose": normalized_purpose,
                "status": "confirmed_demo",
                "dataSource": DATA_SOURCE,
                "dataNotice": DEMO_NOTICE,
            }
            self._bookings.append(booking)

            # Do not return internal patient identity in the booking response.
            return {
                key: value
                for key, value in booking.items()
                if key != "patientId"
            }

    def get_patient_bookings(self, patient_id: str) -> list[dict[str, Any]]:
        """Return only the authenticated patient's demo bookings."""
        self._validate_patient(patient_id)

        with self._lock:
            own_bookings = [
                dict(booking)
                for booking in self._bookings
                if booking["patientId"] == patient_id
                and booking["status"] == "confirmed_demo"
            ]

        own_bookings.sort(
            key=lambda item: (item["date"], item["time"])
        )
        for booking in own_bookings:
            booking.pop("patientId", None)

        return own_bookings


demo_scheduler = DemoScheduler()
