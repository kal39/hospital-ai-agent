"""Tests for staff review of synthetic patient appointment requests."""

from datetime import date, timedelta
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.data.scheduling import DOCTORS
from app.services.demo_scheduler import DemoScheduler


STAFF_REQUESTS_URL = "/api/staff/appointment-requests"
PATIENT_REQUESTS_URL = "/api/patient/appointment-requests"
STAFF_TOKEN = "test-only-staff-secret"


@pytest.fixture
def client(monkeypatch):
    import app.core.auth as auth
    import app.api.appointment_requests as requests_api

    scheduler = DemoScheduler(db_path=":memory:")
    monkeypatch.setattr(requests_api, "demo_scheduler", scheduler)
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
        yield test_client

    scheduler._connection.close()


@pytest.fixture
def staff_headers():
    return {"X-Demo-Staff-Token": STAFF_TOKEN}


def patient_headers(patient_id="patient-001"):
    return {"X-Demo-Patient-Id": patient_id}


def submit_request(client, patient_id="patient-001", **overrides):
    start = date.today() + timedelta(days=7)
    end = date.today() + timedelta(days=14)

    payload = {
        "department": "General Medicine",
        "preferredDoctor": "No preference",
        "preferredDateStart": start.isoformat(),
        "preferredDateEnd": end.isoformat(),
        "reason": "I would like an additional follow-up appointment.",
    }
    payload.update(overrides)

    response = client.post(
        PATIENT_REQUESTS_URL,
        headers=patient_headers(patient_id),
        json=payload,
    )
    assert response.status_code == 201, response.text
    return response.json()["request"]


def next_weekday(offset=7):
    selected = date.today() + timedelta(days=offset)
    while selected.weekday() >= 5:
        selected += timedelta(days=1)
    return selected.isoformat()


def test_staff_request_list_requires_staff_authentication(client):
    assert client.get(STAFF_REQUESTS_URL).status_code == 401
    assert client.get(
        STAFF_REQUESTS_URL,
        headers=patient_headers(),
    ).status_code == 401


def test_staff_can_list_patient_requests(client, staff_headers):
    request = submit_request(client)

    response = client.get(
        STAFF_REQUESTS_URL,
        headers=staff_headers,
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert isinstance(body["requests"], list)
    assert any(
        item["requestId"] == request["requestId"]
        for item in body["requests"]
    )


def test_staff_can_approve_request_and_create_booking(
    client, staff_headers
):
    request = submit_request(client)
    doctor = next(
        item for item in DOCTORS
        if item["department"] == request["department"]
    )

    response = client.post(
        f"{STAFF_REQUESTS_URL}/{request['requestId']}/approve",
        headers=staff_headers,
        json={
            "doctorId": doctor["id"],
            "date": next_weekday(),
            "time": "09:00",
        },
    )

    assert response.status_code == 200, response.text
    body = response.json()
    approved = body.get("request", body)

    assert approved["status"] in {"approved", "approved_demo", "booked", "appointment_confirmed"}
    assert approved.get("bookingId") or approved.get("booking", {}).get("bookingId")


def test_staff_can_decline_request_with_reason(client, staff_headers):
    request = submit_request(client)

    response = client.post(
        f"{STAFF_REQUESTS_URL}/{request['requestId']}/decline",
        headers=staff_headers,
        json={"reason": "Please contact the clinic for a suitable date."},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    declined = body.get("request", body)
    assert declined["status"] == "declined"


def test_staff_cannot_approve_with_wrong_department_doctor(
    client, staff_headers
):
    request = submit_request(client)
    wrong_doctor = next(
        item for item in DOCTORS
        if item["department"] != request["department"]
    )

    response = client.post(
        f"{STAFF_REQUESTS_URL}/{request['requestId']}/approve",
        headers=staff_headers,
        json={
            "doctorId": wrong_doctor["id"],
            "date": next_weekday(),
            "time": "09:00",
        },
    )

    assert response.status_code in {400, 409, 422}, response.text

    patient_response = client.get(
        f"{PATIENT_REQUESTS_URL}/{request['requestId']}",
        headers=patient_headers(),
    )
    assert patient_response.status_code == 200
    assert patient_response.json()["request"]["status"] == "submitted"


def test_request_cannot_be_decided_twice(client, staff_headers):
    request = submit_request(client)

    first = client.post(
        f"{STAFF_REQUESTS_URL}/{request['requestId']}/decline",
        headers=staff_headers,
        json={"reason": "Please contact the clinic to discuss availability."},
    )
    assert first.status_code == 200, first.text

    second = client.post(
        f"{STAFF_REQUESTS_URL}/{request['requestId']}/decline",
        headers=staff_headers,
        json={"reason": "Please contact the clinic to discuss availability."},
    )
    assert second.status_code == 409, second.text


def test_staff_approval_rejects_same_patient_time_with_different_doctor(
    client, staff_headers
):
    import app.api.appointment_requests as requests_api

    appointment_date = next_weekday()
    requests_api.demo_scheduler.book_appointment(
        patient_id="patient-001",
        doctor_id="doctor-001",
        appointment_date=appointment_date,
        appointment_time="09:00",
    )

    request = submit_request(client)
    response = client.post(
        f"{STAFF_REQUESTS_URL}/{request['requestId']}/approve",
        headers=staff_headers,
        json={
            "doctorId": "doctor-002",
            "date": appointment_date,
            "time": "09:00",
        },
    )

    assert response.status_code == 409, response.text
    assert "already have a confirmed appointment at this date and time" in response.json()["detail"]

    current = client.get(
        f"{PATIENT_REQUESTS_URL}/{request['requestId']}",
        headers=patient_headers(),
    )
    assert current.status_code == 200
    assert current.json()["request"]["status"] == "submitted"

    active = requests_api.demo_scheduler.get_patient_bookings("patient-001")
    assert len(active) == 1
    assert active[0]["doctorId"] == "doctor-001"


def test_invalid_staff_token_is_rejected(client):
    response = client.get(
        STAFF_REQUESTS_URL,
        headers={"X-Demo-Staff-Token": "incorrect-token"},
    )
    assert response.status_code == 401


def test_approval_booking_failure_preserves_request(
    client, staff_headers, monkeypatch
):
    import app.api.appointment_requests as requests_api

    request = submit_request(client)
    doctor = next(
        item for item in DOCTORS
        if item["department"] == request["department"]
    )

    def fail_booking(**kwargs):
        raise ValueError("Simulated scheduler failure")

    monkeypatch.setattr(requests_api.demo_scheduler, "book_appointment", fail_booking)

    response = client.post(
        f"{STAFF_REQUESTS_URL}/{request['requestId']}/approve",
        headers=staff_headers,
        json={
            "doctorId": doctor["id"],
            "date": next_weekday(),
            "time": "09:00",
        },
    )

    assert response.status_code >= 400, response.text

    current = client.get(
        f"{PATIENT_REQUESTS_URL}/{request['requestId']}",
        headers=patient_headers(),
    )
    assert current.status_code == 200
    assert current.json()["request"]["status"] == "submitted"



def test_approval_cannot_create_duplicate_booking(client, staff_headers):
    import app.api.appointment_requests as requests_api

    request = submit_request(client)
    doctor = next(
        item for item in DOCTORS
        if item["department"] == request["department"]
    )

    payload = {
        "doctorId": doctor["id"],
        "date": next_weekday(),
        "time": "09:00",
    }
    url = f"{STAFF_REQUESTS_URL}/{request['requestId']}/approve"

    first = client.post(url, headers=staff_headers, json=payload)

    assert first.status_code == 200, first.text

    first_body = first.json()
    first_request = first_body.get("request", first_body)
    first_booking_id = (
        first_request.get("bookingId")
        or first_request.get("booking", {}).get("bookingId")
    )

    assert first_booking_id

    second = client.post(url, headers=staff_headers, json=payload)

    assert second.status_code == 409, second.text

    bookings = requests_api.demo_scheduler.get_patient_bookings(
        "patient-001",
        include_inactive=True,
    )

    assert len(bookings) == 1
    assert bookings[0]["bookingId"] == first_booking_id


def test_approval_rolls_back_booking_when_request_save_fails(
    client, staff_headers, monkeypatch
):
    import app.api.appointment_requests as requests_api

    request = submit_request(client)
    doctor = next(
        item for item in DOCTORS
        if item["department"] == request["department"]
    )

    service = requests_api._request_service()

    def fail_save(record):
        raise RuntimeError("Simulated request persistence failure")

    monkeypatch.setattr(service, "_save_record", fail_save)

    with pytest.raises(
        RuntimeError,
        match="Simulated request persistence failure",
    ):
        client.post(
            f"{STAFF_REQUESTS_URL}/{request['requestId']}/approve",
            headers=staff_headers,
            json={
                "doctorId": doctor["id"],
                "date": next_weekday(),
                "time": "09:00",
            },
        )

    current = client.get(
        f"{PATIENT_REQUESTS_URL}/{request['requestId']}",
        headers=patient_headers(),
    )

    assert current.status_code == 200
    assert current.json()["request"]["status"] == "submitted"

    bookings = requests_api.demo_scheduler.get_patient_bookings(
        "patient-001",
        include_inactive=True,
    )

    assert bookings == []

def test_approving_request_creates_patient_notification(client, staff_headers):
    import app.api.appointment_requests as requests_api
    from app.services.notifications import get_notification_service

    request = submit_request(client)
    doctor = next(
        item for item in DOCTORS
        if item["department"] == request["department"]
    )

    response = client.post(
        f"{STAFF_REQUESTS_URL}/{request['requestId']}/approve",
        headers=staff_headers,
        json={
            "doctorId": doctor["id"],
            "date": next_weekday(),
            "time": "09:00",
        },
    )

    assert response.status_code == 200, response.text

    notifications = get_notification_service(
        requests_api.demo_scheduler
    ).list_patient_notifications("patient-001")

    matching = [
        item for item in notifications
        if item["requestId"] == request["requestId"]
    ]

    assert len(matching) == 1
    assert matching[0]["eventType"] == "appointment_approved"
    assert matching[0]["bookingId"] is not None
    assert matching[0]["deliveryStatus"] == "demo_created"


def test_declining_request_creates_patient_notification(client, staff_headers):
    import app.api.appointment_requests as requests_api
    from app.services.notifications import get_notification_service

    request = submit_request(client)
    reason = "Please contact the clinic to discuss another date."

    response = client.post(
        f"{STAFF_REQUESTS_URL}/{request['requestId']}/decline",
        headers=staff_headers,
        json={"reason": reason},
    )

    assert response.status_code == 200, response.text

    notifications = get_notification_service(
        requests_api.demo_scheduler
    ).list_patient_notifications("patient-001")

    matching = [
        item for item in notifications
        if item["requestId"] == request["requestId"]
    ]

    assert len(matching) == 1
    assert matching[0]["eventType"] == "appointment_declined"
    assert reason in matching[0]["message"]
    assert matching[0]["deliveryStatus"] == "demo_created"


def test_requesting_additional_information_requires_staff_authentication(client):
    request = submit_request(client)

    response = client.post(
        f"{STAFF_REQUESTS_URL}/{request['requestId']}/request-information",
        json={"message": "Please provide your preferred appointment dates."},
    )

    assert response.status_code == 401


def test_staff_can_request_additional_information_and_notify_patient(
    client, staff_headers
):
    import app.api.appointment_requests as requests_api
    from app.services.notifications import get_notification_service

    request = submit_request(client)
    message = (
        "Please provide your preferred appointment dates "
        "so the clinic can review your request."
    )

    response = client.post(
        f"{STAFF_REQUESTS_URL}/{request['requestId']}/request-information",
        headers=staff_headers,
        json={"message": message},
    )

    assert response.status_code == 200, response.text

    updated = response.json()["request"]
    assert updated["status"] == "needs_information"
    assert any(
        item["status"] == "needs_information"
        and item["note"] == message
        for item in updated["statusHistory"]
    )

    patient_response = client.get(
        f"{PATIENT_REQUESTS_URL}/{request['requestId']}",
        headers=patient_headers("patient-001"),
    )

    assert patient_response.status_code == 200
    patient_request = patient_response.json()["request"]
    assert patient_request["status"] == "needs_information"
    assert any(
        item["note"] == message
        for item in patient_request["statusHistory"]
    )

    notifications = get_notification_service(
        requests_api.demo_scheduler
    ).list_patient_notifications("patient-001")

    matching = [
        item for item in notifications
        if item["requestId"] == request["requestId"]
    ]

    assert len(matching) == 1
    assert matching[0]["eventType"] == "additional_information_requested"
    assert matching[0]["message"] == message
    assert matching[0]["bookingId"] is None
    assert matching[0]["deliveryStatus"] == "demo_created"

    other_patient_notifications = get_notification_service(
        requests_api.demo_scheduler
    ).list_patient_notifications("patient-002")

    assert not any(
        item["requestId"] == request["requestId"]
        for item in other_patient_notifications
    )


@pytest.mark.parametrize(
    "message",
    [
        "",
        "   ",
        "Short",
        "x" * 1001,
    ],
)
def test_requesting_additional_information_validates_message(
    client, staff_headers, message
):
    request = submit_request(client)

    response = client.post(
        f"{STAFF_REQUESTS_URL}/{request['requestId']}/request-information",
        headers=staff_headers,
        json={"message": message},
    )

    assert response.status_code == 422, response.text

    current = client.get(
        f"{PATIENT_REQUESTS_URL}/{request['requestId']}",
        headers=patient_headers(),
    )

    assert current.status_code == 200
    assert current.json()["request"]["status"] == "submitted"


def test_staff_cannot_request_information_after_request_is_declined(
    client, staff_headers
):
    request = submit_request(client)

    declined = client.post(
        f"{STAFF_REQUESTS_URL}/{request['requestId']}/decline",
        headers=staff_headers,
        json={"reason": "Please contact the clinic to discuss another date."},
    )
    assert declined.status_code == 200, declined.text

    response = client.post(
        f"{STAFF_REQUESTS_URL}/{request['requestId']}/request-information",
        headers=staff_headers,
        json={"message": "Please provide your preferred appointment dates."},
    )

    assert response.status_code == 409, response.text
