
"""SQLite-backed scheduler for fictional local demonstration appointments.

All records are synthetic. This is not a production hospital scheduling system.
Use an authorized hospital scheduling API for production.
"""

import json
import os
import sqlite3
from datetime import date, datetime, timezone
from pathlib import Path
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


class BookingNotFoundError(Exception):
    """The booking does not exist or does not belong to the patient."""


class BookingConflictError(Exception):
    """The requested booking operation conflicts with its current state."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _validate_not_in_past(
    selected_date: date,
    appointment_time: str,
    now: datetime | None = None,
) -> None:
    """Reject demo appointment slots whose local time has passed."""
    current = now if now is not None else datetime.now().astimezone()
    selected_time = datetime.strptime(appointment_time, "%H:%M").time()
    current_time = current.time().replace(
        tzinfo=None,
        second=0,
        microsecond=0,
    )

    if selected_date < current.date():
        raise ValueError("Appointments cannot be booked in the past.")

    if selected_date == current.date() and selected_time <= current_time:
        raise ValueError("This demo appointment time has already passed.")


class DemoScheduler:
    """Thread-safe SQLite scheduler for the local prototype.

    Instantiate with no argument for an isolated in-memory database.
    The shared application instance uses HOSPITAL_DEMO_DATABASE_PATH.
    """

    def __init__(self, db_path: str = ":memory:") -> None:
        self._lock = RLock()
        self._db_path = db_path

        if db_path != ":memory:":
            Path(db_path).expanduser().resolve().parent.mkdir(
                parents=True,
                exist_ok=True,
            )

        self._connection = sqlite3.connect(
            db_path,
            check_same_thread=False,
            timeout=10,
        )
        self._connection.row_factory = sqlite3.Row

        with self._lock:
            self._connection.execute(
                """
                CREATE TABLE IF NOT EXISTS demo_bookings (
                    booking_id TEXT PRIMARY KEY,
                    patient_id TEXT NOT NULL,
                    doctor_id TEXT NOT NULL,
                    appointment_date TEXT NOT NULL,
                    appointment_time TEXT NOT NULL,
                    status TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            self._connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_demo_bookings_patient
                ON demo_bookings(patient_id, appointment_date, appointment_time)
                """
            )
            self._connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_demo_bookings_slot
                ON demo_bookings(doctor_id, appointment_date, appointment_time, status)
                """
            )
            self._connection.commit()

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

    @staticmethod
    def _public_booking(booking: dict[str, Any]) -> dict[str, Any]:
        """Never expose internal patient identity in a booking response."""
        return {
            key: value
            for key, value in booking.items()
            if key != "patientId"
        }

    def _rows_for_day(
        self,
        doctor_id: str,
        appointment_date: str,
    ) -> list[dict[str, Any]]:
        rows = self._connection.execute(
            """
            SELECT payload_json FROM demo_bookings
            WHERE doctor_id = ?
              AND appointment_date = ?
              AND status = 'confirmed_demo'
            """,
            (doctor_id, appointment_date),
        ).fetchall()
        return [json.loads(row["payload_json"]) for row in rows]

    def _rows_for_slot(
        self,
        doctor_id: str,
        appointment_date: str,
        appointment_time: str,
    ) -> list[dict[str, Any]]:
        return [
            booking
            for booking in self._rows_for_day(doctor_id, appointment_date)
            if booking["time"] == appointment_time
        ]

    def _insert_booking(
        self,
        patient_id: str,
        doctor: dict[str, Any],
        selected_date: str,
        appointment_time: str,
        purpose: str,
        history: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        timestamp = _now()
        booking = {
            "bookingId": f"demo-{uuid4().hex[:12]}",
            "patientId": patient_id,
            "doctorId": doctor["id"],
            "doctorName": doctor["name"],
            "department": doctor["department"],
            "location": doctor["location"],
            "date": selected_date,
            "time": appointment_time,
            "purpose": purpose,
            "status": "confirmed_demo",
            "history": history or [
                {
                    "event": "booked",
                    "at": timestamp,
                    "note": "Synthetic demo booking created.",
                }
            ],
            "createdAt": timestamp,
            "updatedAt": timestamp,
            "dataSource": DATA_SOURCE,
            "dataNotice": DEMO_NOTICE,
        }

        self._connection.execute(
            """
            INSERT INTO demo_bookings (
                booking_id, patient_id, doctor_id,
                appointment_date, appointment_time, status,
                payload_json, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                booking["bookingId"],
                patient_id,
                doctor["id"],
                selected_date,
                appointment_time,
                booking["status"],
                json.dumps(booking),
                timestamp,
                timestamp,
            ),
        )
        return booking

    def _update_booking(self, booking: dict[str, Any]) -> None:
        booking["updatedAt"] = _now()
        self._connection.execute(
            """
            UPDATE demo_bookings
            SET status = ?, payload_json = ?, updated_at = ?
            WHERE booking_id = ?
            """,
            (
                booking["status"],
                json.dumps(booking),
                booking["updatedAt"],
                booking["bookingId"],
            ),
        )

    def get_slot_status(
        self,
        doctor_id: str,
        appointment_date: str,
        appointment_time: str,
    ) -> dict[str, Any]:
        """Return slot capacity without disclosing other patients."""
        self._doctor(doctor_id)
        self._validate_date(appointment_date)
        self._validate_time(appointment_time)

        with self._lock:
            day_bookings = self._rows_for_day(doctor_id, appointment_date)
            slot_bookings = self._rows_for_slot(
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
            "dailyRemainingCapacity": DAILY_CAPACITY_PER_DOCTOR - len(day_bookings),
            "available": len(slot_bookings) < SLOT_CAPACITY,
            "dataSource": DATA_SOURCE,
            "dataNotice": DEMO_NOTICE,
        }

    def get_day_summary(
        self,
        doctor_id: str,
        appointment_date: str,
    ) -> dict[str, Any]:
        """Return aggregate synthetic bookings and an illustrative queue estimate."""
        doctor = self._doctor(doctor_id)
        selected_date = self._validate_date(appointment_date)

        with self._lock:
            booked_count = len(
                self._rows_for_day(doctor_id, selected_date.isoformat())
            )

        people_ahead = (
            DEMO_QUEUE_PEOPLE_AHEAD if selected_date.weekday() < 5 else 0
        )

        return {
            "doctorId": doctor_id,
            "doctorName": doctor["name"],
            "date": selected_date.isoformat(),
            "bookedCount": booked_count,
            "dailyCapacity": DAILY_CAPACITY_PER_DOCTOR,
            "remainingCapacity": DAILY_CAPACITY_PER_DOCTOR - booked_count,
            "illustrativeQueueCount": people_ahead,
            "illustrativeWaitMinutes": people_ahead * DEMO_MINUTES_PER_PATIENT,
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
        """Create a demo booking after the caller confirms the specific slot."""
        self._validate_patient(patient_id)
        doctor = self._doctor(doctor_id)
        selected_date = self._validate_date(appointment_date).isoformat()
        self._validate_time(appointment_time)
        _validate_not_in_past(
            date.fromisoformat(selected_date),
            appointment_time,
        )

        normalized_purpose = purpose.strip()
        if len(normalized_purpose) > 200:
            raise ValueError("Appointment purpose must be 200 characters or fewer.")

        with self._lock:
            self._connection.execute("BEGIN IMMEDIATE")
            try:
                day_bookings = self._rows_for_day(doctor_id, selected_date)

                if len(day_bookings) >= DAILY_CAPACITY_PER_DOCTOR:
                    raise ValueError("This doctor's demo daily capacity is full.")

                duplicate = self._connection.execute(
                    """
                    SELECT 1 FROM demo_bookings
                    WHERE patient_id = ? AND doctor_id = ?
                      AND appointment_date = ? AND appointment_time = ?
                      AND status = 'confirmed_demo'
                    LIMIT 1
                    """,
                    (patient_id, doctor_id, selected_date, appointment_time),
                ).fetchone()
                if duplicate:
                    raise ValueError(
                        "You already have a demo booking for this doctor, "
                        "date, and time."
                    )

                slot_bookings = self._rows_for_slot(
                    doctor_id,
                    selected_date,
                    appointment_time,
                )
                if len(slot_bookings) >= SLOT_CAPACITY:
                    raise ValueError("This demo time slot is full.")

                booking = self._insert_booking(
                    patient_id,
                    doctor,
                    selected_date,
                    appointment_time,
                    normalized_purpose,
                )
                self._connection.commit()
            except Exception:
                self._connection.rollback()
                raise

        return self._public_booking(booking)

    def get_patient_bookings(
        self,
        patient_id: str,
        include_inactive: bool = False,
    ) -> list[dict[str, Any]]:
        """Return only this patient's bookings."""
        self._validate_patient(patient_id)

        query = """
            SELECT payload_json FROM demo_bookings
            WHERE patient_id = ?
        """
        if not include_inactive:
            query += " AND status = 'confirmed_demo'"
        query += " ORDER BY appointment_date, appointment_time"

        with self._lock:
            rows = self._connection.execute(query, (patient_id,)).fetchall()

        bookings = [json.loads(row["payload_json"]) for row in rows]
        return [self._public_booking(item) for item in bookings]

    def get_patient_booking(
        self,
        patient_id: str,
        booking_id: str,
    ) -> dict[str, Any]:
        """Get one booking only when it belongs to the patient."""
        self._validate_patient(patient_id)

        with self._lock:
            row = self._connection.execute(
                """
                SELECT payload_json FROM demo_bookings
                WHERE booking_id = ? AND patient_id = ?
                """,
                (booking_id, patient_id),
            ).fetchone()

        if row is None:
            raise BookingNotFoundError("Appointment not found.")
        return self._public_booking(json.loads(row["payload_json"]))

    def cancel_appointment(
        self,
        patient_id: str,
        booking_id: str,
    ) -> dict[str, Any]:
        """Cancel an active booking owned by the patient."""
        self._validate_patient(patient_id)

        with self._lock:
            self._connection.execute("BEGIN IMMEDIATE")
            try:
                row = self._connection.execute(
                    """
                    SELECT payload_json FROM demo_bookings
                    WHERE booking_id = ? AND patient_id = ?
                    """,
                    (booking_id, patient_id),
                ).fetchone()

                if row is None:
                    raise BookingNotFoundError("Appointment not found.")

                booking = json.loads(row["payload_json"])
                if booking["status"] != "confirmed_demo":
                    raise BookingConflictError(
                        "Only an active demo appointment can be cancelled."
                    )

                booking["status"] = "cancelled_demo"
                booking.setdefault("history", []).append(
                    {
                        "event": "cancelled",
                        "at": _now(),
                        "note": "Cancelled by patient in the demo portal.",
                    }
                )
                self._update_booking(booking)
                self._connection.commit()
            except Exception:
                self._connection.rollback()
                raise

        return self._public_booking(booking)

    def reschedule_appointment(
        self,
        patient_id: str,
        booking_id: str,
        doctor_id: str,
        appointment_date: str,
        appointment_time: str,
    ) -> dict[str, Any]:
        """Atomically replace a patient's active demo booking with a new slot."""
        self._validate_patient(patient_id)
        doctor = self._doctor(doctor_id)
        selected_date = self._validate_date(appointment_date).isoformat()
        self._validate_time(appointment_time)
        _validate_not_in_past(
            date.fromisoformat(selected_date),
            appointment_time,
        )

        with self._lock:
            self._connection.execute("BEGIN IMMEDIATE")
            try:
                row = self._connection.execute(
                    """
                    SELECT payload_json FROM demo_bookings
                    WHERE booking_id = ? AND patient_id = ?
                    """,
                    (booking_id, patient_id),
                ).fetchone()

                if row is None:
                    raise BookingNotFoundError("Appointment not found.")

                old_booking = json.loads(row["payload_json"])
                if old_booking["status"] != "confirmed_demo":
                    raise BookingConflictError(
                        "Only an active demo appointment can be rescheduled."
                    )

                if (
                    old_booking["doctorId"] == doctor_id
                    and old_booking["date"] == selected_date
                    and old_booking["time"] == appointment_time
                ):
                    raise BookingConflictError(
                        "Choose a different doctor, date, or time."
                    )

                old_booking["status"] = "rescheduled_demo"
                old_booking.setdefault("history", []).append(
                    {
                        "event": "rescheduled",
                        "at": _now(),
                        "note": "Replaced by a new demo appointment.",
                    }
                )
                self._update_booking(old_booking)

                day_bookings = self._rows_for_day(doctor_id, selected_date)
                if len(day_bookings) >= DAILY_CAPACITY_PER_DOCTOR:
                    raise BookingConflictError(
                        "This doctor's demo daily capacity is full."
                    )

                duplicate = self._connection.execute(
                    """
                    SELECT 1 FROM demo_bookings
                    WHERE patient_id = ? AND doctor_id = ?
                      AND appointment_date = ? AND appointment_time = ?
                      AND status = 'confirmed_demo'
                    LIMIT 1
                    """,
                    (patient_id, doctor_id, selected_date, appointment_time),
                ).fetchone()
                if duplicate:
                    raise BookingConflictError(
                        "You already have a demo booking for this doctor, "
                        "date, and time."
                    )

                slot_bookings = self._rows_for_slot(
                    doctor_id,
                    selected_date,
                    appointment_time,
                )
                if len(slot_bookings) >= SLOT_CAPACITY:
                    raise BookingConflictError("This demo time slot is full.")

                new_booking = self._insert_booking(
                    patient_id=patient_id,
                    doctor=doctor,
                    selected_date=selected_date,
                    appointment_time=appointment_time,
                    purpose=old_booking.get("purpose", ""),
                    history=[
                        {
                            "event": "rescheduled_from",
                            "at": _now(),
                            "previousBookingId": booking_id,
                            "note": "New fictional demo appointment.",
                        }
                    ],
                )
                self._connection.commit()
            except Exception:
                self._connection.rollback()
                raise

        return {
            "previousBooking": self._public_booking(old_booking),
            "booking": self._public_booking(new_booking),
            "dataSource": DATA_SOURCE,
            "dataNotice": DEMO_NOTICE,
        }


# The shared application instance uses a persistent local SQLite file.
# Set HOSPITAL_DEMO_DATABASE_PATH=:memory: to disable disk persistence.
_database_path = os.getenv(
    "HOSPITAL_DEMO_DATABASE_PATH",
    "data/appointments.sqlite3",
)
demo_scheduler = DemoScheduler(db_path=_database_path)
