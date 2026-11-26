"""API tests for synthetic in-portal notifications."""

from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.demo_scheduler import DemoScheduler
from app.services.notifications import get_notification_service


PATIENT_NOTIFICATIONS_URL = "/api/patient/notifications"
STAFF_NOTIFICATIONS_URL = "/api/staff/notifications"
STAFF_TOKEN = "test-only-staff-secret"


@pytest.fixture
def scheduler_and_client(monkeypatch):
    import app.core.auth as auth
    import app.api.notifications as notifications_api

    scheduler = DemoScheduler(db_path=":memory:")
    monkeypatch.setattr(notifications_api, "demo_scheduler", scheduler)
    monkeypatch.setattr(
        auth,
        "get_settings",
        lambda: SimpleNamespace(
            environment="development",
            demo_auth_enabled=True,
            demo_staff_token=STAFF_TOKEN,
        ),
    )

    with TestClient(app) as test_client:
        yield scheduler, test_client

    scheduler._connection.close()


@pytest.fixture
def staff_headers():
    return {"X-Demo-Staff-Token": STAFF_TOKEN}


def patient_headers(patient_id="patient-001"):
    return {"X-Demo-Patient-Id": patient_id}


def create_notification(scheduler, patient_id="patient-001", **overrides):
    payload = {
        "event_type": "appointment_approved",
        "title": "Appointment approved",
        "message": "Your appointment has been approved.",
        "booking_id": "booking-demo-001",
    }
    payload.update(overrides)

    return get_notification_service(scheduler).create_notification(
        patient_id=patient_id,
        **payload,
    )


def test_patient_notification_list_requires_patient_authentication(
    scheduler_and_client,
):
    _, client = scheduler_and_client

    assert client.get(PATIENT_NOTIFICATIONS_URL).status_code == 401


def test_patient_can_list_only_their_own_notifications(
    scheduler_and_client,
):
    scheduler, client = scheduler_and_client

    own = create_notification(scheduler, "patient-001")
    create_notification(
        scheduler,
        "patient-002",
        title="Another patient's notification",
    )

    response = client.get(
        PATIENT_NOTIFICATIONS_URL,
        headers=patient_headers("patient-001"),
    )

    assert response.status_code == 200, response.text
    notifications = response.json()["notifications"]

    assert any(
        item["notificationId"] == own["notificationId"]
        for item in notifications
    )
    assert all("patientId" not in item for item in notifications)
    assert all(
        item["notificationId"] != "another-patient-notification"
        for item in notifications
    )


def test_patient_can_filter_unread_notifications(scheduler_and_client):
    scheduler, client = scheduler_and_client
    service = get_notification_service(scheduler)

    read_item = create_notification(scheduler)
    unread_item = create_notification(
        scheduler,
        title="New appointment reminder",
        event_type="appointment_reminder",
    )
    service.mark_patient_notification_read(
        notification_id=read_item["notificationId"],
        patient_id="patient-001",
    )

    response = client.get(
        PATIENT_NOTIFICATIONS_URL,
        headers=patient_headers(),
        params={"unread_only": True},
    )

    assert response.status_code == 200, response.text
    notifications = response.json()["notifications"]
    ids = {item["notificationId"] for item in notifications}

    assert unread_item["notificationId"] in ids
    assert read_item["notificationId"] not in ids


def test_patient_can_mark_own_notification_as_read(scheduler_and_client):
    scheduler, client = scheduler_and_client
    item = create_notification(scheduler)

    response = client.post(
        f"{PATIENT_NOTIFICATIONS_URL}/{item['notificationId']}/read",
        headers=patient_headers(),
    )

    assert response.status_code == 200, response.text
    notification = response.json()["notification"]

    assert notification["notificationId"] == item["notificationId"]
    assert notification["isRead"] is True
    assert notification["readAt"] is not None


def test_patient_cannot_mark_another_patients_notification_as_read(
    scheduler_and_client,
):
    scheduler, client = scheduler_and_client
    item = create_notification(scheduler, "patient-002")

    response = client.post(
        f"{PATIENT_NOTIFICATIONS_URL}/{item['notificationId']}/read",
        headers=patient_headers("patient-001"),
    )

    assert response.status_code == 404, response.text


def test_patient_read_endpoint_returns_404_for_unknown_notification(
    scheduler_and_client,
):
    _, client = scheduler_and_client

    response = client.post(
        f"{PATIENT_NOTIFICATIONS_URL}/missing-notification/read",
        headers=patient_headers(),
    )

    assert response.status_code == 404


def test_staff_notification_list_requires_staff_authentication(
    scheduler_and_client,
):
    _, client = scheduler_and_client

    assert client.get(STAFF_NOTIFICATIONS_URL).status_code == 401
    assert client.get(
        STAFF_NOTIFICATIONS_URL,
        headers=patient_headers(),
    ).status_code == 401


def test_staff_can_list_notifications_with_patient_identity(
    scheduler_and_client,
    staff_headers,
):
    scheduler, client = scheduler_and_client
    item = create_notification(scheduler)

    response = client.get(
        STAFF_NOTIFICATIONS_URL,
        headers=staff_headers,
    )

    assert response.status_code == 200, response.text
    notifications = response.json()["notifications"]

    matching = next(
        entry for entry in notifications
        if entry["notificationId"] == item["notificationId"]
    )
    assert matching["patientId"] == "patient-001"


def test_staff_can_filter_notifications_by_patient(
    scheduler_and_client,
    staff_headers,
):
    scheduler, client = scheduler_and_client
    first = create_notification(scheduler, "patient-001")
    second = create_notification(scheduler, "patient-002")

    response = client.get(
        STAFF_NOTIFICATIONS_URL,
        headers=staff_headers,
        params={"patient_id": "patient-001"},
    )

    assert response.status_code == 200, response.text
    notifications = response.json()["notifications"]
    ids = {item["notificationId"] for item in notifications}

    assert first["notificationId"] in ids
    assert second["notificationId"] not in ids


def test_staff_can_filter_notifications_by_event_type(
    scheduler_and_client,
    staff_headers,
):
    scheduler, client = scheduler_and_client
    approved = create_notification(
        scheduler,
        event_type="appointment_approved",
    )
    create_notification(
        scheduler,
        event_type="appointment_reminder",
        title="Appointment reminder",
    )

    response = client.get(
        STAFF_NOTIFICATIONS_URL,
        headers=staff_headers,
        params={"event_type": "appointment_approved"},
    )

    assert response.status_code == 200, response.text
    notifications = response.json()["notifications"]

    assert all(
        item["eventType"] == "appointment_approved"
        for item in notifications
    )
    assert any(
        item["notificationId"] == approved["notificationId"]
        for item in notifications
    )


def test_staff_can_filter_unread_notifications(
    scheduler_and_client,
    staff_headers,
):
    scheduler, client = scheduler_and_client
    service = get_notification_service(scheduler)

    read_item = create_notification(scheduler)
    unread_item = create_notification(
        scheduler,
        title="New reminder",
        event_type="appointment_reminder",
    )
    service.mark_patient_notification_read(
        notification_id=read_item["notificationId"],
        patient_id="patient-001",
    )

    response = client.get(
        STAFF_NOTIFICATIONS_URL,
        headers=staff_headers,
        params={"unread_only": True},
    )

    assert response.status_code == 200, response.text
    ids = {
        item["notificationId"]
        for item in response.json()["notifications"]
    }

    assert unread_item["notificationId"] in ids
    assert read_item["notificationId"] not in ids


def test_invalid_staff_notification_filter_is_rejected(
    scheduler_and_client,
    staff_headers,
):
    _, client = scheduler_and_client

    response = client.get(
        STAFF_NOTIFICATIONS_URL,
        headers=staff_headers,
        params={"event_type": "not-a-valid-event"},
    )

    assert response.status_code == 422
