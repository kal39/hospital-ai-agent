"""SQLite-backed appointment request management for synthetic demos."""

import copy
import json
from datetime import UTC, date, datetime
from typing import Any
from uuid import uuid4

from app.data.patients import PATIENTS
from app.services.audit import record_audit_event
from app.data.scheduling import DATA_SOURCE


DATA_NOTICE = (
    "SYNTHETIC DEMONSTRATION DATA: This request is stored in the local demo "
    "SQLite database and persists across backend restarts. It has not been "
    "sent to a real hospital, reviewed by real hospital staff, or confirmed "
    "as a real appointment."
)

REQUEST_STATUSES = {
    "submitted",
    "under_review",
    "needs_information",
    "appointment_offered",
    "declined",
    "cancelled",
    "appointment_confirmed",
}

PATIENT_CANCELLABLE_STATUSES = {
    "submitted",
    "under_review",
    "needs_information",
    "appointment_offered",
}


class AppointmentRequestError(Exception):
    """Base exception for appointment request operations."""


class AppointmentRequestNotFound(AppointmentRequestError):
    """Raised when a request does not exist or is not owned by the patient."""


class AppointmentRequestConflict(AppointmentRequestError):
    """Raised when an operation is invalid for the current request state."""


class DemoAppointmentRequestService:
    """Persistent request store sharing the scheduler's SQLite connection."""

    def __init__(self, scheduler: Any) -> None:
        self._scheduler = scheduler
        self._connection = scheduler._connection
        self._lock = scheduler._lock

        with self._lock:
            self._connection.execute(
                """
                CREATE TABLE IF NOT EXISTS demo_appointment_requests (
                    request_id TEXT PRIMARY KEY,
                    patient_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    submitted_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                )
                """
            )
            self._connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_demo_appointment_requests_patient
                ON demo_appointment_requests(patient_id, submitted_at)
                """
            )
            self._connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_demo_appointment_requests_status
                ON demo_appointment_requests(status, submitted_at)
                """
            )
            self._connection.commit()

    @staticmethod
    def _public_request(record: dict[str, Any]) -> dict[str, Any]:
        """Return a patient-safe copy without internal ownership fields."""
        result = copy.deepcopy(record)
        result.pop("patientId", None)
        return result

    def _load_record(self, request_id: str) -> dict[str, Any] | None:
        row = self._connection.execute(
            """
            SELECT payload_json
            FROM demo_appointment_requests
            WHERE request_id = ?
            """,
            (request_id,),
        ).fetchone()

        if row is None:
            return None

        return json.loads(row[0])

    def _save_record(self, record: dict[str, Any]) -> None:
        """Insert or update one request inside the caller's transaction."""
        self._connection.execute(
            """
            INSERT INTO demo_appointment_requests (
                request_id,
                patient_id,
                status,
                submitted_at,
                updated_at,
                payload_json
            )
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(request_id) DO UPDATE SET
                patient_id = excluded.patient_id,
                status = excluded.status,
                submitted_at = excluded.submitted_at,
                updated_at = excluded.updated_at,
                payload_json = excluded.payload_json
            """,
            (
                record["requestId"],
                record["patientId"],
                record["status"],
                record["submittedAt"],
                record["updatedAt"],
                json.dumps(record, ensure_ascii=False),
            ),
        )

    def create_request(
        self,
        *,
        patient_id: str,
        department: str | None,
        preferred_doctor: str | None,
        preferred_date_start: date | None,
        preferred_date_end: date | None,
        reason: str,
    ) -> dict[str, Any]:
        if patient_id not in PATIENTS:
            raise ValueError("Unknown synthetic patient.")

        today = date.today()

        if preferred_date_start and preferred_date_start < today:
            raise ValueError("The preferred start date cannot be in the past.")

        if preferred_date_end and preferred_date_end < today:
            raise ValueError("The preferred end date cannot be in the past.")

        if (
            preferred_date_start
            and preferred_date_end
            and preferred_date_end < preferred_date_start
        ):
            raise ValueError(
                "The preferred end date must be on or after the start date."
            )

        now = datetime.now(UTC).isoformat()
        request_id = f"demo-req-{uuid4().hex[:12]}"

        record: dict[str, Any] = {
            "requestId": request_id,
            "patientId": patient_id,
            "department": department,
            "preferredDoctor": preferred_doctor,
            "preferredDateStart": (
                preferred_date_start.isoformat()
                if preferred_date_start else None
            ),
            "preferredDateEnd": (
                preferred_date_end.isoformat()
                if preferred_date_end else None
            ),
            "reason": reason,
            "status": "submitted",
            "submittedAt": now,
            "updatedAt": now,
            "statusHistory": [
                {
                    "status": "submitted",
                    "timestamp": now,
                    "note": "Request submitted in the synthetic demo.",
                }
            ],
            "dataSource": DATA_SOURCE,
            "dataNotice": DATA_NOTICE,
        }

        with self._lock:
            self._connection.execute("BEGIN IMMEDIATE")
            try:
                self._save_record(record)
                self._connection.commit()
            except Exception:
                self._connection.rollback()
                raise

        record_audit_event(
            {
                "patientId": patient_id,
                "event": "appointment_request_submitted",
                "details": {
                    "requestId": request_id,
                    "status": "submitted",
                    "dataSource": DATA_SOURCE,
                },
            }
        )

        return self._public_request(record)

    def list_patient_requests(
        self,
        patient_id: str,
    ) -> list[dict[str, Any]]:
        if patient_id not in PATIENTS:
            raise ValueError("Unknown synthetic patient.")

        with self._lock:
            rows = self._connection.execute(
                """
                SELECT payload_json
                FROM demo_appointment_requests
                WHERE patient_id = ?
                ORDER BY submitted_at DESC
                """,
                (patient_id,),
            ).fetchall()

        return [
            self._public_request(json.loads(row[0]))
            for row in rows
        ]

    def get_patient_request(
        self,
        *,
        patient_id: str,
        request_id: str,
    ) -> dict[str, Any]:
        with self._lock:
            record = self._load_record(request_id)

            if record is None or record["patientId"] != patient_id:
                raise AppointmentRequestNotFound

            return self._public_request(record)

    def cancel_patient_request(
        self,
        *,
        patient_id: str,
        request_id: str,
    ) -> dict[str, Any]:
        with self._lock:
            self._connection.execute("BEGIN IMMEDIATE")
            try:
                record = self._load_record(request_id)

                if record is None or record["patientId"] != patient_id:
                    raise AppointmentRequestNotFound

                if record["status"] not in PATIENT_CANCELLABLE_STATUSES:
                    raise AppointmentRequestConflict(
                        "This request can no longer be cancelled through "
                        "the patient request workflow."
                    )

                now = datetime.now(UTC).isoformat()
                record["status"] = "cancelled"
                record["updatedAt"] = now
                record["statusHistory"].append(
                    {
                        "status": "cancelled",
                        "timestamp": now,
                        "note": "Cancelled by the patient in the synthetic demo.",
                    }
                )

                self._save_record(record)
                result = self._public_request(record)
                self._connection.commit()

            except Exception:
                self._connection.rollback()
                raise

        record_audit_event(
            {
                "patientId": patient_id,
                "event": "appointment_request_cancelled",
                "details": {
                    "requestId": request_id,
                    "status": "cancelled",
                    "dataSource": DATA_SOURCE,
                },
            }
        )

        return result

    def list_staff_requests(self) -> list[dict[str, Any]]:
        """List requests for authorized demo staff, including patient identity."""
        with self._lock:
            rows = self._connection.execute(
                """
                SELECT payload_json
                FROM demo_appointment_requests
                ORDER BY submitted_at DESC
                """
            ).fetchall()

        return [json.loads(row[0]) for row in rows]

    def approve_request(
        self,
        *,
        request_id: str,
        doctor: dict[str, Any],
        appointment_date: str,
        appointment_time: str,
        booking_factory: Any,
        decided_by: str,
    ) -> dict[str, Any]:
        """Atomically create a booking and confirm its appointment request."""
        with self._lock:
            self._connection.execute("BEGIN IMMEDIATE")

            try:
                record = self._load_record(request_id)

                if record is None:
                    raise AppointmentRequestNotFound

                if record["status"] not in {
                    "submitted",
                    "under_review",
                    "needs_information",
                }:
                    raise AppointmentRequestConflict(
                        "This request has already been decided or is no longer eligible."
                    )

                requested_department = record.get("department")
                if (
                    requested_department
                    and requested_department.casefold()
                    != doctor["department"].casefold()
                ):
                    raise ValueError(
                        "The selected doctor's department does not match the request."
                    )

                # The scheduler joins this transaction because its connection
                # is already inside BEGIN IMMEDIATE.
                booking = booking_factory(
                    patient_id=record["patientId"],
                    doctor_id=doctor["id"],
                    appointment_date=appointment_date,
                    appointment_time=appointment_time,
                    purpose=record["reason"][:200],
                )

                now = datetime.now(UTC).isoformat()
                record["status"] = "appointment_confirmed"
                record["bookingId"] = booking["bookingId"]
                record["assignedDoctorId"] = doctor["id"]
                record["assignedDoctorName"] = doctor["name"]
                record["appointmentDate"] = booking["date"]
                record["appointmentTime"] = booking["time"]
                record["updatedAt"] = now
                record["statusHistory"].append(
                    {
                        "status": "appointment_confirmed",
                        "timestamp": now,
                        "note": (
                            "A synthetic demo appointment was assigned "
                            "by authorized demo staff."
                        ),
                        "decidedBy": decided_by,
                        "bookingId": booking["bookingId"],
                    }
                )

                self._save_record(record)
                result = self._public_request(record)
                result["booking"] = booking

                self._connection.commit()

            except Exception:
                self._connection.rollback()
                raise

        record_audit_event(
            {
                "patientId": record["patientId"],
                "event": "appointment_request_approved",
                "details": {
                    "status": "appointment_confirmed",
                    "dataSource": DATA_SOURCE,
                },
            }
        )

        return result

    def decline_request(
        self,
        *,
        request_id: str,
        reason: str,
        decided_by: str,
    ) -> dict[str, Any]:
        """Decline an eligible request and retain the staff's reason."""
        with self._lock:
            self._connection.execute("BEGIN IMMEDIATE")

            try:
                record = self._load_record(request_id)

                if record is None:
                    raise AppointmentRequestNotFound

                if record["status"] not in {
                    "submitted",
                    "under_review",
                    "needs_information",
                }:
                    raise AppointmentRequestConflict(
                        "This request has already been decided or is no longer eligible."
                    )

                now = datetime.now(UTC).isoformat()
                record["status"] = "declined"
                record["declineReason"] = reason
                record["updatedAt"] = now
                record["statusHistory"].append(
                    {
                        "status": "declined",
                        "timestamp": now,
                        "note": reason,
                        "decidedBy": decided_by,
                    }
                )

                self._save_record(record)
                result = self._public_request(record)
                self._connection.commit()

            except Exception:
                self._connection.rollback()
                raise

        record_audit_event(
            {
                "patientId": record["patientId"],
                "event": "appointment_request_declined",
                "details": {
                    "status": "declined",
                    "dataSource": DATA_SOURCE,
                },
            }
        )

        return result


def get_appointment_request_service(scheduler: Any) -> DemoAppointmentRequestService:
    """Return the persistent request service associated with this scheduler."""
    service = getattr(scheduler, "_appointment_request_service", None)

    if service is None:
        service = DemoAppointmentRequestService(scheduler)
        scheduler._appointment_request_service = service

    return service
