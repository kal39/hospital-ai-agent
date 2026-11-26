from datetime import datetime

import pytest

from app.services.demo_scheduler import DemoScheduler
from app.services.notifications import (
    NOTIFICATION_EVENT_TYPES,
    NotificationNotFound,
    get_notification_service,
)


@pytest.fixture
def scheduler():
    instance = DemoScheduler(db_path=":memory:")
    yield instance
    instance._connection.close()


@pytest.fixture
def notifications(scheduler):
    return get_notification_service(scheduler)


def create_notification(service, **overrides):
    arguments = {
        "patient_id": "patient-001",
        "event_type": "appointment_approved",
        "title": "Appointment approved",
        "message": "Your demonstration appointment has been approved.",
        "booking_id": None,
        "request_id": None,
    }
    arguments.update(overrides)
    return service.create_notification(**arguments)


def test_supported_notification_event_types_are_explicit():
    assert NOTIFICATION_EVENT_TYPES == {
        "appointment_approved",
        "appointment_declined",
        "appointment_delayed",
        "appointment_reminder",
        "appointment_rescheduled",
        "appointment_cancelled",
        "additional_information_requested",
    }


def test_notification_creation_marks_record_as_demo_created(notifications):
    record = create_notification(notifications)

    assert record["eventType"] == "appointment_approved"
    assert record["title"] == "Appointment approved"
    assert record["message"]
    assert record["deliveryStatus"] == "demo_created"
    assert record["channel"] == "in_portal"
    assert record["isRead"] is False
    assert record["readAt"] is None
    assert record["notificationId"]
    assert record["createdAt"]


def test_patient_list_contains_only_their_own_notifications(notifications):
    first = create_notification(
        notifications,
        patient_id="patient-001",
    )
    create_notification(
        notifications,
        patient_id="patient-002",
        title="Another patient's notification",
    )

    records = notifications.list_patient_notifications("patient-001")

    assert len(records) == 1
    assert records[0]["notificationId"] == first["notificationId"]
    assert "patientId" not in records[0]


def test_staff_history_can_filter_by_patient(notifications):
    first = create_notification(
        notifications,
        patient_id="patient-001",
    )
    create_notification(
        notifications,
        patient_id="patient-002",
    )

    records = notifications.list_staff_notifications(
        patient_id="patient-001",
    )

    assert len(records) == 1
    assert records[0]["notificationId"] == first["notificationId"]
    assert records[0]["patientId"] == "patient-001"


def test_patient_can_mark_own_notification_as_read(notifications):
    created = create_notification(notifications)

    updated = notifications.mark_patient_notification_read(
        notification_id=created["notificationId"],
        patient_id="patient-001",
    )

    assert updated["isRead"] is True
    assert updated["readAt"]

    parsed = datetime.fromisoformat(updated["readAt"])
    assert parsed.tzinfo is not None


def test_patient_cannot_mark_another_patients_notification_as_read(
    notifications,
):
    created = create_notification(
        notifications,
        patient_id="patient-001",
    )

    with pytest.raises(NotificationNotFound):
        notifications.mark_patient_notification_read(
            notification_id=created["notificationId"],
            patient_id="patient-002",
        )

    own_record = notifications.list_patient_notifications("patient-001")
    assert own_record[0]["isRead"] is False


def test_marking_notification_read_twice_is_idempotent(notifications):
    created = create_notification(notifications)

    first = notifications.mark_patient_notification_read(
        notification_id=created["notificationId"],
        patient_id="patient-001",
    )
    second = notifications.mark_patient_notification_read(
        notification_id=created["notificationId"],
        patient_id="patient-001",
    )

    assert first["isRead"] is True
    assert second["isRead"] is True
    assert second["readAt"] == first["readAt"]


def test_unknown_patient_cannot_list_notifications(notifications):
    with pytest.raises(ValueError, match="Unknown synthetic patient"):
        notifications.list_patient_notifications("unknown-patient")


@pytest.mark.parametrize(
    "field,value",
    [
        ("event_type", "unsupported_event"),
        ("title", ""),
        ("message", "   "),
    ],
)
def test_notification_creation_rejects_invalid_values(
    notifications,
    field,
    value,
):
    with pytest.raises(ValueError):
        create_notification(notifications, **{field: value})


def test_notification_service_is_cached_for_scheduler(scheduler):
    first = get_notification_service(scheduler)
    second = get_notification_service(scheduler)

    assert first is second
    assert first._connection is scheduler._connection
    assert first._lock is scheduler._lock


def test_missing_notification_is_not_found(notifications):
    with pytest.raises(NotificationNotFound):
        notifications.mark_patient_notification_read(
            notification_id="missing-notification",
            patient_id="patient-001",
        )

def test_create_delivery_attempt_starts_as_pending(notifications):
    created = create_notification(notifications)

    attempt = notifications.create_delivery_attempt(
        notification_id=created["notificationId"],
        channel="email",
        recipient_masked="t***@example.org",
        provider="test-provider",
    )

    assert attempt["notificationId"] == created["notificationId"]
    assert attempt["channel"] == "email"
    assert attempt["recipientMasked"] == "t***@example.org"
    assert attempt["provider"] == "test-provider"
    assert attempt["status"] == "pending"
    assert attempt["providerMessageId"] is None
    assert attempt["error"] is None
    assert attempt["createdAt"]
    assert attempt["updatedAt"]


def test_delivery_attempt_can_be_marked_sent_and_delivered(notifications):
    created = create_notification(notifications)

    attempt = notifications.create_delivery_attempt(
        notification_id=created["notificationId"],
        channel="sms",
        recipient_masked="+251******5678",
        provider="test-provider",
    )

    sent = notifications.update_delivery_attempt(
        attempt_id=attempt["attemptId"],
        status="sent",
        provider_message_id="provider-message-123",
    )

    assert sent["status"] == "sent"
    assert sent["providerMessageId"] == "provider-message-123"
    assert sent["deliveredAt"] is None

    delivered = notifications.update_delivery_attempt(
        attempt_id=attempt["attemptId"],
        status="delivered",
    )

    assert delivered["status"] == "delivered"
    assert delivered["providerMessageId"] == "provider-message-123"
    assert delivered["deliveredAt"]


def test_delivery_attempt_can_record_failure(notifications):
    created = create_notification(notifications)

    attempt = notifications.create_delivery_attempt(
        notification_id=created["notificationId"],
        channel="email",
        recipient_masked="t***@example.org",
        provider="test-provider",
    )

    failed = notifications.update_delivery_attempt(
        attempt_id=attempt["attemptId"],
        status="failed",
        error="Provider rejected the test message.",
    )

    assert failed["status"] == "failed"
    assert failed["error"] == "Provider rejected the test message."


def test_delivery_history_is_listed_for_notification(notifications):
    created = create_notification(notifications)

    email = notifications.create_delivery_attempt(
        notification_id=created["notificationId"],
        channel="email",
        recipient_masked="t***@example.org",
        provider="email-provider",
    )
    sms = notifications.create_delivery_attempt(
        notification_id=created["notificationId"],
        channel="sms",
        recipient_masked="+251******5678",
        provider="sms-provider",
    )

    attempts = notifications.list_delivery_attempts(
        notification_id=created["notificationId"],
    )

    assert {item["attemptId"] for item in attempts} == {
        email["attemptId"],
        sms["attemptId"],
    }


def test_delivery_attempt_rejects_unknown_notification(notifications):
    with pytest.raises(NotificationNotFound):
        notifications.create_delivery_attempt(
            notification_id="missing-notification",
            channel="email",
            recipient_masked="t***@example.org",
            provider="test-provider",
        )


def test_delivery_attempt_rejects_invalid_channel(notifications):
    created = create_notification(notifications)

    with pytest.raises(ValueError, match="channel"):
        notifications.create_delivery_attempt(
            notification_id=created["notificationId"],
            channel="whatsapp",
            recipient_masked="masked",
            provider="test-provider",
        )


def test_delivery_attempt_rejects_invalid_status(notifications):
    created = create_notification(notifications)

    attempt = notifications.create_delivery_attempt(
        notification_id=created["notificationId"],
        channel="email",
        recipient_masked="t***@example.org",
        provider="test-provider",
    )

    with pytest.raises(ValueError, match="status"):
        notifications.update_delivery_attempt(
            attempt_id=attempt["attemptId"],
            status="delivered_by_assumption",
        )


def test_delivered_attempt_cannot_be_reset_to_pending(notifications):
    created = create_notification(notifications)

    attempt = notifications.create_delivery_attempt(
        notification_id=created["notificationId"],
        channel="email",
        recipient_masked="t***@example.org",
        provider="test-provider",
    )

    notifications.update_delivery_attempt(
        attempt_id=attempt["attemptId"],
        status="sent",
    )
    notifications.update_delivery_attempt(
        attempt_id=attempt["attemptId"],
        status="delivered",
    )

    with pytest.raises(ValueError, match="transition"):
        notifications.update_delivery_attempt(
            attempt_id=attempt["attemptId"],
            status="pending",
        )

