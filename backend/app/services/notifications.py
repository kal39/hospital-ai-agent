"""SQLite-backed in-portal notifications for synthetic demonstrations."""

import copy
import json
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from app.data.patients import PATIENTS


NOTIFICATION_EVENT_TYPES = {
    "appointment_approved",
    "appointment_declined",
    "appointment_delayed",
    "appointment_reminder",
    "appointment_rescheduled",
    "appointment_cancelled",
    "additional_information_requested",
}


class NotificationNotFound(Exception):
    """Raised when a notification does not exist or is not patient-owned."""


class DemoNotificationService:
    """Persistent synthetic notifications sharing the scheduler database."""

    def __init__(self, scheduler: Any) -> None:
        self._scheduler = scheduler
        self._connection = scheduler._connection
        self._lock = scheduler._lock

        with self._lock:
            self._connection.execute(
                """
                CREATE TABLE IF NOT EXISTS demo_notifications (
                    notification_id TEXT PRIMARY KEY,
                    patient_id TEXT NOT NULL,
                    booking_id TEXT,
                    request_id TEXT,
                    event_type TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    is_read INTEGER NOT NULL DEFAULT 0,
                    read_at TEXT,
                    payload_json TEXT NOT NULL
                )
                """
            )

            self._connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_demo_notifications_patient_created
                ON demo_notifications(patient_id, created_at)
                """
            )

            self._connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_demo_notifications_event_created
                ON demo_notifications(event_type, created_at)
                """
            )

            self._connection.execute(
                """
                CREATE TABLE IF NOT EXISTS notification_delivery_attempts (
                    attempt_id TEXT PRIMARY KEY,
                    notification_id TEXT NOT NULL,
                    channel TEXT NOT NULL,
                    recipient_masked TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    status TEXT NOT NULL,
                    provider_message_id TEXT,
                    error TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    delivered_at TEXT,
                    FOREIGN KEY (notification_id)
                        REFERENCES demo_notifications(notification_id)
                )
                """
            )
            self._connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_notification_delivery_attempts_notification
                ON notification_delivery_attempts(notification_id, created_at)
                """
            )
            self._connection.commit()

    @staticmethod
    def _public_notification(
        record: dict[str, Any],
    ) -> dict[str, Any]:
        """Return a patient-safe copy without internal ownership data."""
        result = copy.deepcopy(record)
        result.pop("patientId", None)
        return result

    def _load_record(
        self,
        notification_id: str,
    ) -> dict[str, Any] | None:
        row = self._connection.execute(
            """
            SELECT payload_json
            FROM demo_notifications
            WHERE notification_id = ?
            """,
            (notification_id,),
        ).fetchone()

        if row is None:
            return None

        return json.loads(row[0])

    def _save_record(self, record: dict[str, Any]) -> None:
        """Persist one notification inside the caller's transaction."""
        self._connection.execute(
            """
            INSERT INTO demo_notifications (
                notification_id,
                patient_id,
                booking_id,
                request_id,
                event_type,
                created_at,
                is_read,
                read_at,
                payload_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record["notificationId"],
                record["patientId"],
                record["bookingId"],
                record["requestId"],
                record["eventType"],
                record["createdAt"],
                int(record["isRead"]),
                record["readAt"],
                json.dumps(record, ensure_ascii=False),
            ),
        )

    def create_notification(
        self,
        *,
        patient_id: str,
        event_type: str,
        title: str,
        message: str,
        booking_id: str | None = None,
        request_id: str | None = None,
    ) -> dict[str, Any]:
        """Create a synthetic in-portal notification for one patient."""

        if not isinstance(patient_id, str) or patient_id not in PATIENTS:
            raise ValueError("Unknown synthetic patient.")

        if (
            not isinstance(event_type, str)
            or event_type not in NOTIFICATION_EVENT_TYPES
        ):
            raise ValueError("Unsupported notification event type.")

        if (
            not isinstance(title, str)
            or not title.strip()
            or len(title.strip()) > 160
        ):
            raise ValueError("Notification title must be 1-160 characters.")

        if (
            not isinstance(message, str)
            or not message.strip()
            or len(message.strip()) > 2000
        ):
            raise ValueError("Notification message must be 1-2000 characters.")

        for field_name, value in (
            ("booking_id", booking_id),
            ("request_id", request_id),
        ):
            if value is not None and (
                not isinstance(value, str)
                or not value.strip()
                or len(value) > 128
            ):
                raise ValueError(f"Invalid notification {field_name}.")

        now = datetime.now(UTC).isoformat()

        record = {
            "notificationId": f"demo-notif-{uuid4().hex[:12]}",
            "patientId": patient_id,
            "bookingId": booking_id,
            "requestId": request_id,
            "eventType": event_type,
            "title": title.strip(),
            "message": message.strip(),
            "channel": "in_portal",
            "deliveryStatus": "demo_created",
            "createdAt": now,
            "isRead": False,
            "readAt": None,
        }

        with self._lock:
            self._connection.execute("BEGIN IMMEDIATE")
            try:
                self._save_record(record)
                self._connection.commit()
            except Exception:
                self._connection.rollback()
                raise

        return self._public_notification(record)

    def list_patient_notifications(
        self,
        patient_id: str,
        *,
        unread_only: bool = False,
    ) -> list[dict[str, Any]]:
        """List only notifications belonging to the authenticated patient."""

        if not isinstance(patient_id, str) or patient_id not in PATIENTS:
            raise ValueError("Unknown synthetic patient.")

        query = """
            SELECT payload_json
            FROM demo_notifications
            WHERE patient_id = ?
        """
        parameters: list[Any] = [patient_id]

        if unread_only:
            query += " AND is_read = 0"

        query += " ORDER BY created_at DESC, notification_id DESC"

        with self._lock:
            rows = self._connection.execute(
                query,
                parameters,
            ).fetchall()

        return [
            self._public_notification(json.loads(row[0]))
            for row in rows
        ]

    def list_staff_notifications(
        self,
        *,
        patient_id: str | None = None,
        event_type: str | None = None,
        unread_only: bool | None = None,
    ) -> list[dict[str, Any]]:
        """List notification history for the authorized staff workflow."""

        if patient_id is not None:
            if not isinstance(patient_id, str) or patient_id not in PATIENTS:
                raise ValueError("Unknown synthetic patient.")

        if event_type is not None and event_type not in NOTIFICATION_EVENT_TYPES:
            raise ValueError("Unsupported notification event type.")

        if unread_only is not None and not isinstance(unread_only, bool):
            raise ValueError("unread_only must be a boolean.")

        query = "SELECT payload_json FROM demo_notifications WHERE 1 = 1"
        parameters: list[Any] = []

        if patient_id is not None:
            query += " AND patient_id = ?"
            parameters.append(patient_id)

        if event_type is not None:
            query += " AND event_type = ?"
            parameters.append(event_type)

        if unread_only is not None:
            query += " AND is_read = ?"
            parameters.append(0 if unread_only else 1)

        query += " ORDER BY created_at DESC, notification_id DESC"

        with self._lock:
            rows = self._connection.execute(
                query,
                parameters,
            ).fetchall()

        return [json.loads(row[0]) for row in rows]

    def mark_patient_notification_read(
        self,
        *,
        notification_id: str,
        patient_id: str,
    ) -> dict[str, Any]:
        """Mark one notification read, enforcing patient ownership."""

        if not isinstance(patient_id, str) or patient_id not in PATIENTS:
            raise ValueError("Unknown synthetic patient.")

        if (
            not isinstance(notification_id, str)
            or not notification_id.strip()
            or len(notification_id) > 128
        ):
            raise NotificationNotFound

        with self._lock:
            self._connection.execute("BEGIN IMMEDIATE")

            try:
                record = self._load_record(notification_id)

                if record is None or record["patientId"] != patient_id:
                    raise NotificationNotFound

                if not record["isRead"]:
                    record["isRead"] = True
                    record["readAt"] = datetime.now(UTC).isoformat()

                    self._connection.execute(
                        """
                        UPDATE demo_notifications
                        SET is_read = 1,
                            read_at = ?,
                            payload_json = ?
                        WHERE notification_id = ?
                          AND patient_id = ?
                        """,
                        (
                            record["readAt"],
                            json.dumps(record, ensure_ascii=False),
                            notification_id,
                            patient_id,
                        ),
                    )

                self._connection.commit()

            except Exception:
                self._connection.rollback()
                raise

        return self._public_notification(record)


    def create_delivery_attempt(
        self,
        *,
        notification_id: str,
        channel: str,
        recipient_masked: str,
        provider: str,
    ) -> dict[str, Any]:
        """Create a pending outbound delivery attempt."""

        if (
            not isinstance(notification_id, str)
            or not notification_id.strip()
            or len(notification_id) > 128
        ):
            raise NotificationNotFound
        if not isinstance(channel, str) or channel not in {"email", "sms"}:
            raise ValueError("Invalid delivery channel.")
        if (
            not isinstance(recipient_masked, str)
            or not recipient_masked.strip()
            or len(recipient_masked) > 254
        ):
            raise ValueError("Invalid masked delivery recipient.")
        if (
            not isinstance(provider, str)
            or not provider.strip()
            or len(provider.strip()) > 100
        ):
            raise ValueError("Invalid delivery provider.")

        now = datetime.now(UTC).isoformat()
        attempt = {
            "attemptId": f"delivery-{uuid4().hex}",
            "notificationId": notification_id,
            "channel": channel,
            "recipientMasked": recipient_masked.strip(),
            "provider": provider.strip(),
            "status": "pending",
            "providerMessageId": None,
            "error": None,
            "createdAt": now,
            "updatedAt": now,
            "deliveredAt": None,
        }

        with self._lock:
            self._connection.execute("BEGIN IMMEDIATE")
            try:
                if self._load_record(notification_id) is None:
                    raise NotificationNotFound

                self._connection.execute(
                    """
                    INSERT INTO notification_delivery_attempts (
                        attempt_id, notification_id, channel,
                        recipient_masked, provider, status,
                        provider_message_id, error, created_at,
                        updated_at, delivered_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        attempt["attemptId"], notification_id, channel,
                        attempt["recipientMasked"], attempt["provider"],
                        "pending", None, None, now, now, None,
                    ),
                )
                self._connection.commit()
            except Exception:
                self._connection.rollback()
                raise

        return attempt

    def update_delivery_attempt(
        self,
        *,
        attempt_id: str,
        status: str,
        provider_message_id: str | None = None,
        error: str | None = None,
    ) -> dict[str, Any]:
        """Update an attempt while enforcing valid status transitions."""

        transitions = {
            "pending": {
                "pending", "sent", "delivered", "failed", "simulated",
            },
            "sent": {"sent", "delivered", "failed"},
            "delivered": {"delivered"},
            "failed": {"failed"},
            "simulated": {"simulated"},
        }
        if not isinstance(status, str) or status not in transitions:
            raise ValueError("Invalid delivery status.")
        if (
            not isinstance(attempt_id, str)
            or not attempt_id.strip()
            or len(attempt_id) > 128
        ):
            raise ValueError("Invalid delivery attempt ID.")
        if provider_message_id is not None and (
            not isinstance(provider_message_id, str)
            or len(provider_message_id) > 256
        ):
            raise ValueError("Invalid provider message ID.")
        if error is not None and (
            not isinstance(error, str) or len(error) > 1000
        ):
            raise ValueError("Invalid delivery error.")

        keys = (
            "attemptId", "notificationId", "channel",
            "recipientMasked", "provider", "status",
            "providerMessageId", "error", "createdAt",
            "updatedAt", "deliveredAt",
        )

        with self._lock:
            self._connection.execute("BEGIN IMMEDIATE")
            try:
                row = self._connection.execute(
                    """
                    SELECT attempt_id, notification_id, channel,
                           recipient_masked, provider, status,
                           provider_message_id, error, created_at,
                           updated_at, delivered_at
                    FROM notification_delivery_attempts
                    WHERE attempt_id = ?
                    """,
                    (attempt_id,),
                ).fetchone()

                if row is None:
                    raise NotificationNotFound

                attempt = dict(zip(keys, row))
                if status not in transitions[attempt["status"]]:
                    raise ValueError("Invalid delivery status transition.")

                now = datetime.now(UTC).isoformat()
                attempt["status"] = status
                attempt["updatedAt"] = now

                if provider_message_id is not None:
                    attempt["providerMessageId"] = provider_message_id
                if error is not None:
                    attempt["error"] = error
                if status == "delivered" and attempt["deliveredAt"] is None:
                    attempt["deliveredAt"] = now

                self._connection.execute(
                    """
                    UPDATE notification_delivery_attempts
                    SET status = ?, provider_message_id = ?, error = ?,
                        updated_at = ?, delivered_at = ?
                    WHERE attempt_id = ?
                    """,
                    (
                        attempt["status"], attempt["providerMessageId"],
                        attempt["error"], attempt["updatedAt"],
                        attempt["deliveredAt"], attempt_id,
                    ),
                )
                self._connection.commit()
            except Exception:
                self._connection.rollback()
                raise

        return attempt

    def list_delivery_attempts(
        self,
        *,
        notification_id: str,
    ) -> list[dict[str, Any]]:
        """Return delivery attempts for one existing notification."""

        if (
            not isinstance(notification_id, str)
            or not notification_id.strip()
            or len(notification_id) > 128
        ):
            raise NotificationNotFound

        keys = (
            "attemptId", "notificationId", "channel",
            "recipientMasked", "provider", "status",
            "providerMessageId", "error", "createdAt",
            "updatedAt", "deliveredAt",
        )

        with self._lock:
            if self._load_record(notification_id) is None:
                raise NotificationNotFound

            rows = self._connection.execute(
                """
                SELECT attempt_id, notification_id, channel,
                       recipient_masked, provider, status,
                       provider_message_id, error, created_at,
                       updated_at, delivered_at
                FROM notification_delivery_attempts
                WHERE notification_id = ?
                ORDER BY created_at ASC, attempt_id ASC
                """,
                (notification_id,),
            ).fetchall()

        return [dict(zip(keys, row)) for row in rows]


def get_notification_service(
    scheduler: Any,
) -> DemoNotificationService:
    """Return the notification service cached on its scheduler."""

    service = getattr(scheduler, "_notification_service", None)

    if service is None:
        service = DemoNotificationService(scheduler)
        scheduler._notification_service = service

    return service
