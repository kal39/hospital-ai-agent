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


demo_appointment_request_service = DemoAppointmentRequestService()
