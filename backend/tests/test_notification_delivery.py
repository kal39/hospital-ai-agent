"""Tests for provider-independent outbound notification delivery."""

from types import SimpleNamespace

import pytest

from app.core.config import Settings
from app.services.notification_delivery import (
    DEMO_NOTICE_LABEL,
    DeliveryResult,
    NotificationDeliveryDispatcher,
)


class FakeEmailSender:
    def __init__(self, result=None):
        self.calls = []
        self.result = result or DeliveryResult(
            status="sent",
            provider_message_id="email-test-001",
        )

    def send_email(self, *, recipient, subject, text):
        self.calls.append({
            "recipient": recipient,
            "subject": subject,
            "text": text,
        })
        return self.result


class FakeSmsSender:
    def __init__(self, result=None):
        self.calls = []
        self.result = result or DeliveryResult(
            status="sent",
            provider_message_id="sms-test-001",
        )

    def send_sms(self, *, recipient, message):
        self.calls.append({
            "recipient": recipient,
            "message": message,
        })
        return self.result


def make_notification():
    return {
        "title": "Appointment approved",
        "message": "Your demonstration appointment was approved.",
        "patientId": "patient-001",
        "patientEmail": "must-not-be-used@example.org",
        "patientPhone": "+251911111111",
    }


def test_disabled_channels_do_not_send_messages():
    email = FakeEmailSender()
    sms = FakeSmsSender()

    dispatcher = NotificationDeliveryDispatcher(
        settings=Settings(_env_file=None),
        email_sender=email,
        sms_sender=sms,
    )

    assert dispatcher.dispatch(make_notification()) == []
    assert email.calls == []
    assert sms.calls == []


def test_email_uses_only_the_configured_test_recipient():
    email = FakeEmailSender()
    settings = Settings(
        _env_file=None,
        notification_email_enabled=True,
        notification_email_provider="test-provider",
        notification_email_api_key="test-key",
        notification_email_from="demo@example.org",
        notification_test_email="tester@example.org",
    )

    dispatcher = NotificationDeliveryDispatcher(
        settings=settings,
        email_sender=email,
    )

    deliveries = dispatcher.dispatch(make_notification())

    assert len(deliveries) == 1
    assert deliveries[0].channel == "email"
    assert deliveries[0].recipient == "tester@example.org"
    assert deliveries[0].result.status == "sent"
    assert email.calls[0]["recipient"] == "tester@example.org"
    assert DEMO_NOTICE_LABEL in email.calls[0]["subject"]
    assert DEMO_NOTICE_LABEL in email.calls[0]["text"]
    assert "must-not-be-used@example.org" not in email.calls[0]["text"]
    assert "+251911111111" not in email.calls[0]["text"]


def test_sms_uses_only_the_configured_test_phone():
    sms = FakeSmsSender()
    settings = Settings(
        _env_file=None,
        notification_sms_enabled=True,
        notification_sms_provider="test-provider",
        notification_sms_api_key="test-key",
        notification_sms_sender_id="HOSPITAL",
        notification_test_phone="+251912345678",
    )

    dispatcher = NotificationDeliveryDispatcher(
        settings=settings,
        sms_sender=sms,
    )

    deliveries = dispatcher.dispatch(make_notification())

    assert len(deliveries) == 1
    assert deliveries[0].channel == "sms"
    assert deliveries[0].recipient == "+251912345678"
    assert deliveries[0].result.status == "sent"
    assert sms.calls[0]["recipient"] == "+251912345678"
    assert DEMO_NOTICE_LABEL in sms.calls[0]["message"]
    assert "must-not-be-used@example.org" not in sms.calls[0]["message"]
    assert "+251911111111" not in sms.calls[0]["message"]


def test_email_and_sms_can_be_dispatched_independently():
    email = FakeEmailSender()
    sms = FakeSmsSender()

    settings = Settings(
        _env_file=None,
        notification_email_enabled=True,
        notification_email_provider="test-provider",
        notification_email_api_key="test-key",
        notification_email_from="demo@example.org",
        notification_test_email="tester@example.org",
        notification_sms_enabled=True,
        notification_sms_provider="test-provider",
        notification_sms_api_key="test-key",
        notification_sms_sender_id="HOSPITAL",
        notification_test_phone="+251912345678",
    )

    dispatcher = NotificationDeliveryDispatcher(
        settings=settings,
        email_sender=email,
        sms_sender=sms,
    )

    deliveries = dispatcher.dispatch(make_notification())

    assert [item.channel for item in deliveries] == ["email", "sms"]
    assert len(email.calls) == 1
    assert len(sms.calls) == 1


@pytest.mark.parametrize("status", ["sent", "delivered", "failed"])
def test_delivery_result_accepts_explicit_provider_statuses(status):
    result = DeliveryResult(status=status)
    assert result.status == status


def test_delivery_result_rejects_unknown_status():
    with pytest.raises(ValueError, match="Unsupported"):
        DeliveryResult(status="delivered_by_assumption")


def test_enabled_email_without_adapter_fails_closed():
    settings = Settings(
        _env_file=None,
        notification_email_enabled=True,
        notification_email_provider="test-provider",
        notification_email_api_key="test-key",
        notification_email_from="demo@example.org",
        notification_test_email="tester@example.org",
    )

    dispatcher = NotificationDeliveryDispatcher(settings=settings)

    with pytest.raises(RuntimeError, match="no email adapter"):
        dispatcher.dispatch(make_notification())


def test_enabled_sms_without_adapter_fails_closed():
    settings = Settings(
        _env_file=None,
        notification_sms_enabled=True,
        notification_sms_provider="test-provider",
        notification_sms_api_key="test-key",
        notification_sms_sender_id="HOSPITAL",
        notification_test_phone="+251912345678",
    )

    dispatcher = NotificationDeliveryDispatcher(settings=settings)

    with pytest.raises(RuntimeError, match="no SMS adapter"):
        dispatcher.dispatch(make_notification())


def test_invalid_notification_is_rejected_before_dispatch():
    email = FakeEmailSender()
    dispatcher = NotificationDeliveryDispatcher(
        settings=Settings(_env_file=None),
        email_sender=email,
    )

    with pytest.raises(ValueError, match="Notification title"):
        dispatcher.dispatch({"title": " ", "message": "Hello"})

    assert email.calls == []


from app.services.demo_scheduler import DemoScheduler
from app.services.notifications import get_notification_service


def make_persisted_notification(scheduler):
    service = get_notification_service(scheduler)
    notification = service.create_notification(
        patient_id="patient-001",
        event_type="appointment_approved",
        title="Appointment approved",
        message="Your demonstration appointment was approved.",
    )
    return service, notification


def test_dispatch_persists_email_delivery_attempt():
    scheduler = DemoScheduler(db_path=":memory:")
    try:
        service, notification = make_persisted_notification(scheduler)
        email = FakeEmailSender()
        settings = Settings(
            _env_file=None,
            notification_email_enabled=True,
            notification_email_provider="test-provider",
            notification_email_api_key="test-key",
            notification_email_from="demo@example.org",
            notification_test_email="tester@example.org",
        )

        dispatcher = NotificationDeliveryDispatcher(
            settings=settings,
            email_sender=email,
            notification_service=service,
        )

        deliveries = dispatcher.dispatch(notification)
        history = service.list_delivery_attempts(
            notification_id=notification["notificationId"],
        )

        assert len(deliveries) == 1
        assert len(history) == 1
        assert history[0]["channel"] == "email"
        assert history[0]["status"] == "sent"
        assert history[0]["providerMessageId"] == "email-test-001"
        assert "tester@example.org" not in history[0]["recipientMasked"]
    finally:
        scheduler._connection.close()


def test_email_failure_is_persisted_and_sms_is_still_attempted():
    class FailingEmailSender:
        def send_email(self, **kwargs):
            raise RuntimeError("Provider temporarily unavailable")

    scheduler = DemoScheduler(db_path=":memory:")
    try:
        service, notification = make_persisted_notification(scheduler)
        sms = FakeSmsSender()

        settings = Settings(
            _env_file=None,
            notification_email_enabled=True,
            notification_email_provider="email-provider",
            notification_email_api_key="email-key",
            notification_email_from="demo@example.org",
            notification_test_email="tester@example.org",
            notification_sms_enabled=True,
            notification_sms_provider="sms-provider",
            notification_sms_api_key="sms-key",
            notification_sms_sender_id="HOSPITAL",
            notification_test_phone="+251912345678",
        )

        dispatcher = NotificationDeliveryDispatcher(
            settings=settings,
            email_sender=FailingEmailSender(),
            sms_sender=sms,
            notification_service=service,
        )

        deliveries = dispatcher.dispatch(notification)
        history = service.list_delivery_attempts(
            notification_id=notification["notificationId"],
        )

        assert [item.channel for item in deliveries] == ["email", "sms"]
        assert deliveries[0].result.status == "failed"
        assert deliveries[1].result.status == "sent"
        assert len(sms.calls) == 1

        by_channel = {item["channel"]: item for item in history}
        assert by_channel["email"]["status"] == "failed"
        assert "RuntimeError" in by_channel["email"]["error"]
        assert by_channel["sms"]["status"] == "sent"
    finally:
        scheduler._connection.close()


def test_provider_confirmed_delivery_is_persisted_as_delivered():
    scheduler = DemoScheduler(db_path=":memory:")
    try:
        service, notification = make_persisted_notification(scheduler)
        email = FakeEmailSender(
            DeliveryResult(
                status="delivered",
                provider_message_id="email-delivered-001",
            )
        )
        settings = Settings(
            _env_file=None,
            notification_email_enabled=True,
            notification_email_provider="test-provider",
            notification_email_api_key="test-key",
            notification_email_from="demo@example.org",
            notification_test_email="tester@example.org",
        )

        dispatcher = NotificationDeliveryDispatcher(
            settings=settings,
            email_sender=email,
            notification_service=service,
        )

        dispatcher.dispatch(notification)
        history = service.list_delivery_attempts(
            notification_id=notification["notificationId"],
        )

        assert len(history) == 1
        assert history[0]["status"] == "delivered"
        assert history[0]["providerMessageId"] == "email-delivered-001"
        assert history[0]["deliveredAt"]
    finally:
        scheduler._connection.close()

def test_sample_sms_adapter_records_simulation_only():
    from app.services.notification_delivery import (
        NotificationDeliveryDispatcher,
    )

    scheduler = DemoScheduler(db_path=":memory:")
    try:
        service, notification = make_persisted_notification(scheduler)

        settings = Settings(
            _env_file=None,
            notification_sms_enabled=True,
            notification_sms_provider="sample",
            notification_test_phone="+251900000000",
        )

        dispatcher = NotificationDeliveryDispatcher(
            settings=settings,
            notification_service=service,
        )

        deliveries = dispatcher.dispatch(notification)
        history = service.list_delivery_attempts(
            notification_id=notification["notificationId"],
        )

        assert len(deliveries) == 1
        assert deliveries[0].channel == "sms"
        assert deliveries[0].result.status == "simulated"
        assert deliveries[0].result.provider_message_id is None

        assert len(history) == 1
        assert history[0]["channel"] == "sms"
        assert history[0]["provider"] == "sample"
        assert history[0]["status"] == "simulated"
        assert history[0]["providerMessageId"] is None
        assert history[0]["deliveredAt"] is None
        assert history[0]["recipientMasked"] == "***0000"

        attempt_id = history[0]["attemptId"]

        with pytest.raises(
            ValueError,
            match="Invalid delivery status transition",
        ):
            service.update_delivery_attempt(
                attempt_id=attempt_id,
                status="sent",
            )

        with pytest.raises(
            ValueError,
            match="Invalid delivery status transition",
        ):
            service.update_delivery_attempt(
                attempt_id=attempt_id,
                status="delivered",
            )

        unchanged = service.list_delivery_attempts(
            notification_id=notification["notificationId"],
        )
        assert unchanged[0]["status"] == "simulated"
        assert unchanged[0]["deliveredAt"] is None
    finally:
        scheduler._connection.close()

