"""Outbound demo notification delivery with persistent attempt history."""

from dataclasses import dataclass
from typing import Protocol, Any

from app.core.config import Settings


DEMO_NOTICE_LABEL = "DEMO / SIMULATED APPOINTMENT NOTICE"

DELIVERY_STATUSES = {"sent", "delivered", "failed", "simulated"}


@dataclass(frozen=True)
class DeliveryResult:
    """Result reported by an outbound delivery adapter."""

    status: str
    provider_message_id: str | None = None
    error: str | None = None

    def __post_init__(self) -> None:
        if self.status not in DELIVERY_STATUSES:
            raise ValueError("Unsupported notification delivery status.")

        if self.provider_message_id is not None:
            if not isinstance(self.provider_message_id, str):
                raise ValueError("Provider message ID must be a string.")

        if self.error is not None:
            if not isinstance(self.error, str):
                raise ValueError("Delivery error must be a string.")


class EmailSender(Protocol):
    """Interface implemented by a transactional email provider."""

    def send_email(
        self,
        *,
        recipient: str,
        subject: str,
        text: str,
    ) -> DeliveryResult:
        ...


class SmsSender(Protocol):
    """Interface implemented by an SMS gateway."""

    def send_sms(
        self,
        *,
        recipient: str,
        message: str,
    ) -> DeliveryResult:
        ...


class SampleSmsSender:
    """Local-only SMS simulation. This adapter never performs network I/O."""

    def send_sms(
        self,
        *,
        recipient: str,
        message: str,
    ) -> DeliveryResult:
        if not isinstance(recipient, str) or not recipient.strip():
            raise ValueError("A simulation recipient is required.")
        if not isinstance(message, str) or not message.strip():
            raise ValueError("An SMS message is required.")

        return DeliveryResult(status="simulated")


@dataclass(frozen=True)
class ChannelDelivery:
    """Outcome for one outbound notification channel."""

    channel: str
    recipient: str
    result: DeliveryResult


class NotificationDeliveryDispatcher:
    """Send demo notices only to explicitly configured test destinations."""

    def __init__(
        self,
        *,
        settings: Settings,
        email_sender: EmailSender | None = None,
        sms_sender: SmsSender | None = None,
        notification_service: Any | None = None,
    ) -> None:
        self._settings = settings
        self._email_sender = email_sender
        self._sms_sender = sms_sender

        if (
            self._sms_sender is None
            and settings.notification_sms_provider == "sample"
        ):
            self._sms_sender = SampleSmsSender()

        self._notification_service = notification_service

    @staticmethod
    def _validate_notification(notification: dict) -> tuple[str, str]:
        if not isinstance(notification, dict):
            raise ValueError("Notification must be a dictionary.")

        title = notification.get("title")
        message = notification.get("message")

        if not isinstance(title, str) or not title.strip():
            raise ValueError("Notification title is required.")

        if not isinstance(message, str) or not message.strip():
            raise ValueError("Notification message is required.")

        return title.strip(), message.strip()

    @staticmethod
    def _mask_recipient(channel: str, recipient: str) -> str:
        if channel == "email":
            local, separator, domain = recipient.partition("@")
            if not separator:
                return "***"
            return f"{local[:1]}***@{domain}"

        return f"***{recipient[-4:]}"

    def _deliver(
        self,
        *,
        notification_id: str | None,
        channel: str,
        recipient: str,
        provider: str,
        sender: Any,
        send_arguments: dict[str, str],
    ) -> ChannelDelivery:
        attempt_id = None

        if self._notification_service is not None:
            if not notification_id:
                raise ValueError(
                    "A persisted notification ID is required for delivery history."
                )

            attempt = self._notification_service.create_delivery_attempt(
                notification_id=notification_id,
                channel=channel,
                recipient_masked=self._mask_recipient(channel, recipient),
                provider=provider,
            )
            attempt_id = attempt["attemptId"]

        try:
            if sender is None:
                if channel == "email":
                    raise RuntimeError("no email adapter is configured.")
                raise RuntimeError("no SMS adapter is configured.")

            if channel == "email":
                result = sender.send_email(**send_arguments)
            else:
                result = sender.send_sms(**send_arguments)

            if not isinstance(result, DeliveryResult):
                raise TypeError(
                    "Delivery adapter returned an unsupported result."
                )

        except Exception as exc:
            result = DeliveryResult(
                status="failed",
                error=f"Provider request failed ({type(exc).__name__}).",
            )

            if attempt_id is None:
                raise RuntimeError(str(exc)) from exc

        if attempt_id is not None:
            self._notification_service.update_delivery_attempt(
                attempt_id=attempt_id,
                status=result.status,
                provider_message_id=result.provider_message_id,
                error=result.error,
            )

        return ChannelDelivery(
            channel=channel,
            recipient=recipient,
            result=result,
        )

    def dispatch(
        self,
        notification: dict,
    ) -> list[ChannelDelivery]:
        """Dispatch independently to configured test destinations.

        When a notification service is supplied, each enabled channel gets a
        persistent attempt before the provider is called. Provider failures
        are recorded and do not prevent another enabled channel from running.

        This method never reads patient contact details.
        """

        title, message = self._validate_notification(notification)
        notification_id = notification.get("notificationId")

        subject = f"{DEMO_NOTICE_LABEL}: {title}"
        body = f"{DEMO_NOTICE_LABEL}\n\n{title}\n\n{message}"

        deliveries: list[ChannelDelivery] = []

        if self._settings.notification_email_enabled:
            recipient = self._settings.notification_test_email
            deliveries.append(
                self._deliver(
                    notification_id=notification_id,
                    channel="email",
                    recipient=recipient,
                    provider=self._settings.notification_email_provider,
                    sender=self._email_sender,
                    send_arguments={
                        "recipient": recipient,
                        "subject": subject,
                        "text": body,
                    },
                )
            )

        if self._settings.notification_sms_enabled:
            recipient = self._settings.notification_test_phone
            sms_message = f"{DEMO_NOTICE_LABEL}\n{title}: {message}"

            deliveries.append(
                self._deliver(
                    notification_id=notification_id,
                    channel="sms",
                    recipient=recipient,
                    provider=self._settings.notification_sms_provider,
                    sender=self._sms_sender,
                    send_arguments={
                        "recipient": recipient,
                        "message": sms_message,
                    },
                )
            )

        return deliveries
