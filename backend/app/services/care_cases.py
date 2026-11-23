"""Patient-isolated synthetic care-case storage and staff workflow."""

import json
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from app.data.patients import PATIENTS
from app.services.audit import record_audit_event
from app.services.safety import suggest_care_case_priority


EMERGENCY_DATA_NOTICE = (
    "SYNTHETIC DEMONSTRATION DATA: This emergency concern is stored only "
    "in the local demo database. It has not been sent to a real hospital, "
    "reviewed by hospital staff, or clinically triaged. Registration does "
    "not confirm that medical assistance has been arranged. If this may "
    "be an emergency, seek immediate medical attention."
)

URGENT_DATA_NOTICE = (
    "SYNTHETIC DEMONSTRATION DATA: This urgent follow-up concern is stored "
    "only in the local demo database. It has not been sent to a real "
    "hospital, reviewed by hospital staff, or clinically triaged. "
    "Registration does not confirm that medical assistance or follow-up "
    "has been arranged. Please contact your healthcare team promptly. "
    "Seek emergency medical care if severe or rapidly worsening symptoms "
    "develop."
)

WORKFLOW_TRANSITIONS = {
    "registered": "acknowledged",
    "acknowledged": "in_review",
    "in_review": "resolved",
}

WORKFLOW_STATUSES = {
    "registered",
    "acknowledged",
    "in_review",
    "resolved",
}


class CareCaseError(Exception):
    """Base exception for synthetic care-case operations."""


class CareCaseConflict(CareCaseError):
    """Raised when a case operation conflicts with its current state."""


class CareCaseNotFound(CareCaseError):
    """Raised when a requested case does not exist."""


class DemoCareCaseService:
    """Persistent patient-isolated care cases with a staff review workflow."""

    def __init__(self, scheduler: Any) -> None:
        self._scheduler = scheduler
        self._connection = scheduler._connection
        self._lock = scheduler._lock

        with self._lock:
            self._connection.execute(
                """
                CREATE TABLE IF NOT EXISTS demo_care_cases (
                    case_id TEXT PRIMARY KEY,
                    patient_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    idempotency_key TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    UNIQUE(patient_id, idempotency_key)
                )
                """
            )
            self._connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_demo_care_cases_patient
                ON demo_care_cases(patient_id, created_at)
                """
            )
            self._connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_demo_care_cases_status
                ON demo_care_cases(status, created_at)
                """
            )
            self._connection.commit()

    @staticmethod
    def _public_case(record: dict[str, Any]) -> dict[str, Any]:
        """Return a patient-safe record without internal staff or ownership data."""
        public_record = dict(record)
        public_record.pop("patientId", None)
        public_record.pop("idempotencyKey", None)
        public_record.pop("staffActionHistory", None)
        public_record.pop("prioritySuggestion", None)
        public_record.pop("priorityReason", None)
        public_record.pop("prioritySource", None)
        public_record.pop("priorityCreatedAt", None)
        return public_record

    @staticmethod
    def _staff_case(record: dict[str, Any]) -> dict[str, Any]:
        """Return staff data with a stored or legacy-derived priority suggestion."""
        staff_record = dict(record)
        staff_record.pop("idempotencyKey", None)

        valid_priorities = {"emergency", "urgent", "routine_review"}
        if staff_record.get("prioritySuggestion") not in valid_priorities:
            suggestion = suggest_care_case_priority(
                str(staff_record.get("reportedConcern", "")),
                str(staff_record.get("language", "en")),
            )
            staff_record.update(suggestion)
            staff_record["prioritySource"] = "prototype_rules"
            staff_record["priorityCreatedAt"] = (
                staff_record.get("createdAt") or ""
            )
        elif not staff_record.get("priorityReason"):
            suggestion = suggest_care_case_priority(
                str(staff_record.get("reportedConcern", "")),
                str(staff_record.get("language", "en")),
            )
            staff_record["priorityReason"] = suggestion["priorityReason"]
            staff_record["prioritySource"] = "prototype_rules"
            staff_record["priorityCreatedAt"] = (
                staff_record.get("priorityCreatedAt")
                or staff_record.get("createdAt")
                or ""
            )

        return staff_record

    def create_case(
        self,
        *,
        patient_id: str,
        conversation_id: str,
        reported_concern: str,
        language: str,
        idempotency_key: str,
        case_type: str = "emergency_concern",
    ) -> dict[str, Any]:
        """Create one synthetic case after explicit patient confirmation."""
        if patient_id not in PATIENTS:
            raise ValueError("Unknown synthetic patient.")

        if not conversation_id or not conversation_id.strip():
            raise ValueError("Conversation identity is required.")

        if not reported_concern or not reported_concern.strip():
            raise ValueError("A reported concern is required.")

        if len(reported_concern) > 2000:
            raise ValueError("Reported concern is too long.")

        if language not in {"en", "am"}:
            raise ValueError("Unsupported language.")

        if not idempotency_key or not idempotency_key.strip():
            raise ValueError("An idempotency key is required.")

        if case_type not in {"emergency_concern", "urgent_concern"}:
            raise ValueError("Unsupported care-case type.")

        concern = reported_concern.strip()
        now = datetime.now(UTC).isoformat()

        record = {
            "caseId": f"demo-case-{uuid4().hex}",
            "caseType": case_type,
            "status": "registered",
            "reportedConcern": concern,
            "conversationId": conversation_id,
            "language": language,
            "createdAt": now,
            "updatedAt": now,
            **suggest_care_case_priority(concern, language),
            "prioritySource": "prototype_rules",
            "priorityCreatedAt": now,
            "dataSource": "synthetic_demo",
            "dataNotice": (
                EMERGENCY_DATA_NOTICE
                if case_type == "emergency_concern"
                else URGENT_DATA_NOTICE
            ),
            "statusHistory": [
                {
                    "status": "registered",
                    "timestamp": now,
                    "note": (
                        "Synthetic demonstration registration only. "
                        "This case has not been clinically triaged."
                    ),
                }
            ],
            "staffActionHistory": [],
            "patientId": patient_id,
            "idempotencyKey": idempotency_key,
        }

        created = False

        with self._lock:
            self._connection.execute("BEGIN IMMEDIATE")

            try:
                existing_row = self._connection.execute(
                    """
                    SELECT payload_json
                    FROM demo_care_cases
                    WHERE patient_id = ? AND idempotency_key = ?
                    """,
                    (patient_id, idempotency_key),
                ).fetchone()

                if existing_row is not None:
                    existing = json.loads(existing_row[0])

                    comparable_fields = (
                        "conversationId",
                        "reportedConcern",
                        "language",
                        "caseType",
                    )

                    if any(
                        existing.get(field) != record.get(field)
                        for field in comparable_fields
                    ):
                        raise CareCaseConflict(
                            "This confirmation key was already used "
                            "for different care-case details."
                        )

                    # Older records may not have this field.
                    existing.setdefault("staffActionHistory", [])
                    record = existing
                else:
                    self._connection.execute(
                        """
                        INSERT INTO demo_care_cases (
                            case_id,
                            patient_id,
                            status,
                            created_at,
                            updated_at,
                            idempotency_key,
                            payload_json
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            record["caseId"],
                            patient_id,
                            record["status"],
                            record["createdAt"],
                            record["updatedAt"],
                            idempotency_key,
                            json.dumps(record, ensure_ascii=False),
                        ),
                    )
                    created = True

                self._connection.commit()

            except Exception:
                self._connection.rollback()
                raise

        if created:
            try:
                record_audit_event(
                    {
                        "patientId": patient_id,
                        "conversationId": conversation_id,
                        "event": (
                            "synthetic_emergency_case_registered"
                            if case_type == "emergency_concern"
                            else "synthetic_urgent_case_registered"
                        ),
                        "details": {
                            "status": record["status"],
                            "dataSource": "synthetic_demo",
                        },
                    }
                )
            except Exception:
                pass

        return self._public_case(record)

    def list_patient_cases(
        self,
        patient_id: str,
    ) -> list[dict[str, Any]]:
        """List only the authenticated patient's synthetic cases."""
        if patient_id not in PATIENTS:
            raise ValueError("Unknown synthetic patient.")

        with self._lock:
            rows = self._connection.execute(
                """
                SELECT payload_json
                FROM demo_care_cases
                WHERE patient_id = ?
                ORDER BY created_at DESC
                """,
                (patient_id,),
            ).fetchall()

        return [
            self._public_case(json.loads(row[0]))
            for row in rows
        ]

    def get_patient_case(
        self,
        *,
        patient_id: str,
        case_id: str,
    ) -> dict[str, Any] | None:
        """Retrieve a case only when it belongs to the requested patient."""
        if patient_id not in PATIENTS:
            raise ValueError("Unknown synthetic patient.")

        with self._lock:
            row = self._connection.execute(
                """
                SELECT payload_json
                FROM demo_care_cases
                WHERE case_id = ? AND patient_id = ?
                """,
                (case_id, patient_id),
            ).fetchone()

        if row is None:
            return None

        return self._public_case(json.loads(row[0]))

    def list_staff_cases(self) -> list[dict[str, Any]]:
        """List all cases for authenticated demo staff, newest first."""
        with self._lock:
            rows = self._connection.execute(
                """
                SELECT payload_json
                FROM demo_care_cases
                ORDER BY created_at DESC, case_id DESC
                """
            ).fetchall()

        return [
            self._staff_case(json.loads(row[0]))
            for row in rows
        ]

    def update_case_status(
        self,
        *,
        case_id: str,
        new_status: str,
        staff_id: str,
        note: str | None = None,
    ) -> dict[str, Any]:
        """Atomically record an authorized staff workflow transition."""
        if new_status not in WORKFLOW_STATUSES:
            raise ValueError("Unsupported care-case workflow status.")

        normalized_staff_id = (
            staff_id.strip() if isinstance(staff_id, str) else ""
        )
        if not normalized_staff_id or len(normalized_staff_id) > 128:
            raise ValueError("A valid staff identity is required.")

        normalized_note = (
            note.strip()
            if isinstance(note, str) and note.strip()
            else None
        )
        if normalized_note and len(normalized_note) > 300:
            raise ValueError("Staff note must be 300 characters or fewer.")

        now = datetime.now(UTC).isoformat()

        with self._lock:
            self._connection.execute("BEGIN IMMEDIATE")

            try:
                row = self._connection.execute(
                    """
                    SELECT payload_json
                    FROM demo_care_cases
                    WHERE case_id = ?
                    """,
                    (case_id,),
                ).fetchone()

                if row is None:
                    raise CareCaseNotFound("Care case not found.")

                record = json.loads(row[0])
                current_status = record.get("status")

                expected_status = WORKFLOW_TRANSITIONS.get(current_status)
                if expected_status != new_status:
                    raise CareCaseConflict(
                        f"Cannot move a case from '{current_status}' "
                        f"to '{new_status}'."
                    )

                action_note = normalized_note or {
                    "acknowledged": "Staff acknowledged receipt.",
                    "in_review": "Staff started reviewing this case.",
                    "resolved": "Staff marked this workflow as resolved.",
                }[new_status]

                patient_status_note = {
                    "acknowledged": "The care case was acknowledged by staff.",
                    "in_review": "The care case is being reviewed by staff.",
                    "resolved": "The care-case workflow was marked as resolved.",
                }[new_status]

                record.setdefault("statusHistory", []).append(
                    {
                        "status": new_status,
                        "timestamp": now,
                        "note": patient_status_note,
                    }
                )

                record.setdefault("staffActionHistory", []).append(
                    {
                        "action": "status_changed",
                        "fromStatus": current_status,
                        "toStatus": new_status,
                        "timestamp": now,
                        "staffId": normalized_staff_id,
                        "note": action_note,
                    }
                )

                record["status"] = new_status
                record["updatedAt"] = now

                self._connection.execute(
                    """
                    UPDATE demo_care_cases
                    SET status = ?, updated_at = ?, payload_json = ?
                    WHERE case_id = ?
                    """,
                    (
                        new_status,
                        now,
                        json.dumps(record, ensure_ascii=False),
                        case_id,
                    ),
                )

                self._connection.commit()

            except Exception:
                self._connection.rollback()
                raise

        try:
            record_audit_event(
                {
                    "event": "synthetic_care_case_status_changed",
                    "patientId": record.get("patientId"),
                    "conversationId": record.get("conversationId"),
                    "details": {
                        "status": new_status,
                        "dataSource": "synthetic_demo",
                    },
                }
            )
        except Exception:
            pass

        return self._staff_case(record)


def get_care_case_service(scheduler: Any) -> DemoCareCaseService:
    """Return the care-case service associated with the active scheduler."""
    service = getattr(scheduler, "_care_case_service", None)

    if service is None:
        service = DemoCareCaseService(scheduler)
        scheduler._care_case_service = service

    return service

