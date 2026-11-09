"""Demo-only patient appointment request management.

Requests are held in memory and are lost when the process restarts.
This module does not create or modify a confirmed hospital appointment.
"""

from datetime import UTC, date, datetime
from threading import RLock
from typing import Any
from uuid import uuid4

from app.data.patients import PATIENTS
from app.services.audit import record_audit_event


DATA_SOURCE = "synthetic_demo"
DATA_NOTICE = (
    "SYNTHETIC DEMONSTRATION DATA: This request is stored locally for "
    "development only. It has not been sent to a real hospital, reviewed "
    "by hospital staff, or confirmed as an appointment. Requests are lost "
    "when the backend restarts."
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
    """Raised when an operation is not valid for the request's current state."""


class DemoAppointmentRequestService:
    """Thread-safe, in-memory appointment request store for local demos."""

    def __init__(self) -> None:
        self._requests: dict[str, dict[str, Any]] = {}
        self._lock = RLock()

    @staticmethod
    def _public_request(record: dict[str, Any]) -> dict[str, Any]:
        """Return a copy without internal ownership fields."""
        result = {
            key: value
            for key, value in record.items()
            if key != "patientId"
        }
        return result

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
                if preferred_date_start
                else None
            ),
            "preferredDateEnd": (
                preferred_date_end.isoformat()
                if preferred_date_end
                else None
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
            self._requests[request_id] = record

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
            records = [
                self._public_request(record)
                for record in self._requests.values()
                if record["patientId"] == patient_id
            ]

        return sorted(
            records,
            key=lambda record: record["submittedAt"],
            reverse=True,
        )

    def get_patient_request(
        self,
        *,
        patient_id: str,
        request_id: str,
    ) -> dict[str, Any]:
        with self._lock:
            record = self._requests.get(request_id)

            # Use the same error for nonexistent and other-patient requests.
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
            record = self._requests.get(request_id)

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
            result = self._public_request(record)

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
            records = [
                dict(record)
                for record in self._requests.values()
            ]

            # Copy nested history so callers cannot mutate stored records.
            import copy
            records = [copy.deepcopy(record) for record in records]

        return sorted(
            records,
            key=lambda record: record["submittedAt"],
            reverse=True,
        )

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
        """Create and link a booking while preventing duplicate request decisions."""
        with self._lock:
            record = self._requests.get(request_id)

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

            # The scheduler validates the patient, date, time, duplicates,
            # and available capacity. If it raises, the request stays unchanged.
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
                    "note": "A synthetic demo appointment was assigned by authorized demo staff.",
                    "decidedBy": decided_by,
                    "bookingId": booking["bookingId"],
                }
            )

            result = self._public_request(record)
            result["booking"] = booking

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
            record = self._requests.get(request_id)

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
            result = self._public_request(record)

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
demo_appointment_request_service = DemoAppointmentRequestService()

