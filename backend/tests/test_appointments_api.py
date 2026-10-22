from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.demo_scheduler import DemoScheduler


@pytest.fixture
def scheduler(monkeypatch):
    import app.api.appointments as appointments_api

    instance = DemoScheduler(db_path=":memory:")
    monkeypatch.setattr(appointments_api, "demo_scheduler", instance)
    yield instance
    instance._connection.close()


@pytest.fixture
def client(scheduler):
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def headers():
    return {"X-Demo-Patient-Id": "patient-001"}


def next_weekday(offset=1):
    selected = date.today() + timedelta(days=offset)
    while selected.weekday() >= 5:
        selected += timedelta(days=1)
    return selected


def available_slot(client, headers, doctor_id):
    start = next_weekday()
    response = client.get(
        "/api/appointments/availability",
        params={
            "doctorId": doctor_id,
            "startDate": start.isoformat(),
            "days": 14,
        },
        headers=headers,
    )
    assert response.status_code == 200, response.text
    slots = [slot for slot in response.json()["slots"] if slot["available"]]
    assert slots, "Expected at least one available synthetic slot."
    return slots[0]


def create_booking(client, headers, doctor_id, slot):
    response = client.post(
        "/api/appointments/book",
        headers=headers,
        json={
            "doctorId": doctor_id,
            "date": slot["date"],
            "time": slot["time"],
            "purpose": "Automated test",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["booking"]


def test_appointment_routes_require_authentication(client):
    paths = [
        "/api/appointments/departments",
        "/api/appointments/doctors",
        "/api/patient/appointments",
    ]
    for path in paths:
        response = client.get(path)
        assert response.status_code == 401, (path, response.text)


def test_departments_and_doctors_are_returned(client, headers):
    departments_response = client.get(
        "/api/appointments/departments", headers=headers
    )
    assert departments_response.status_code == 200
    assert departments_response.json()["departments"]

    doctors_response = client.get("/api/appointments/doctors", headers=headers)
    assert doctors_response.status_code == 200
    doctors = doctors_response.json()["doctors"]
    assert doctors

    department = doctors[0]["department"]
    filtered = client.get(
        "/api/appointments/doctors",
        params={"department": department},
        headers=headers,
    )
    assert filtered.status_code == 200
    assert all(
        doctor["department"] == department
        for doctor in filtered.json()["doctors"]
    )


def test_availability_includes_capacity_and_demo_disclosure(client, headers):
    doctors = client.get(
        "/api/appointments/doctors", headers=headers
    ).json()["doctors"]

    slot = available_slot(client, headers, doctors[0]["id"])
    assert slot["doctorId"] == doctors[0]["id"]
    assert slot["slotCapacity"] > 0
    assert "available" in slot

    response = client.get(
        "/api/appointments/availability",
        params={
            "doctorId": "unknown-doctor",
            "startDate": next_weekday().isoformat(),
        },
        headers=headers,
    )
    assert response.status_code == 422


def test_booking_and_listing_are_patient_scoped(client, headers):
    doctors = client.get(
        "/api/appointments/doctors", headers=headers
    ).json()["doctors"]
    doctor_id = doctors[0]["id"]
    slot = available_slot(client, headers, doctor_id)

    booking = create_booking(client, headers, doctor_id, slot)
    booking_id = booking["bookingId"]

    listing = client.get("/api/patient/appointments", headers=headers)
    assert listing.status_code == 200
    assert any(
        item["bookingId"] == booking_id
        for item in listing.json()["appointments"]
    )
    assert listing.json()["dataSource"] == "synthetic_demo"

    own_detail = client.get(
        f"/api/patient/appointments/{booking_id}", headers=headers
    )
    assert own_detail.status_code == 200

    other_headers = {"X-Demo-Patient-Id": "patient-002"}
    other_detail = client.get(
        f"/api/patient/appointments/{booking_id}",
        headers=other_headers,
    )
    assert other_detail.status_code == 404


def test_client_cannot_inject_patient_identity(client, headers):
    doctors = client.get(
        "/api/appointments/doctors", headers=headers
    ).json()["doctors"]
    slot = available_slot(client, headers, doctors[0]["id"])

    response = client.post(
        "/api/appointments/book",
        headers=headers,
        json={
            "patient_id": "patient-002",
            "doctorId": doctors[0]["id"],
            "date": slot["date"],
            "time": slot["time"],
        },
    )
    assert response.status_code == 422


def test_patient_can_cancel_own_booking(client, headers):
    doctors = client.get(
        "/api/appointments/doctors", headers=headers
    ).json()["doctors"]
    slot = available_slot(client, headers, doctors[0]["id"])
    booking = create_booking(client, headers, doctors[0]["id"], slot)

    response = client.post(
        f"/api/patient/appointments/{booking['bookingId']}/cancel",
        headers=headers,
    )
    assert response.status_code == 200, response.text
    assert response.json()["booking"]["status"] == "cancelled_demo"


def test_patient_cannot_cancel_another_patients_booking(client, headers):
    doctors = client.get(
        "/api/appointments/doctors", headers=headers
    ).json()["doctors"]
    slot = available_slot(client, headers, doctors[0]["id"])
    booking = create_booking(client, headers, doctors[0]["id"], slot)

    response = client.post(
        f"/api/patient/appointments/{booking['bookingId']}/cancel",
        headers={"X-Demo-Patient-Id": "patient-002"},
    )
    assert response.status_code == 404


def test_patient_can_reschedule_own_booking(client, headers):
    doctors = client.get(
        "/api/appointments/doctors", headers=headers
    ).json()["doctors"]
    doctor_id = doctors[0]["id"]
    original_slot = available_slot(client, headers, doctor_id)
    booking = create_booking(client, headers, doctor_id, original_slot)

    start = next_weekday(8)
    response = client.get(
        "/api/appointments/availability",
        params={
            "doctorId": doctor_id,
            "startDate": start.isoformat(),
            "days": 14,
        },
        headers=headers,
    )
    assert response.status_code == 200
    replacement_slots = [
        slot
        for slot in response.json()["slots"]
        if slot["available"]
        and not (
            slot["date"] == original_slot["date"]
            and slot["time"] == original_slot["time"]
        )
    ]
    assert replacement_slots, "Expected an alternative synthetic slot."
    replacement = replacement_slots[0]

    response = client.post(
        f"/api/patient/appointments/{booking['bookingId']}/reschedule",
        headers=headers,
        json={
            "doctorId": doctor_id,
            "date": replacement["date"],
            "time": replacement["time"],
        },
    )
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["previousBooking"]["status"] == "rescheduled_demo"
    assert result["booking"]["status"] == "confirmed_demo"
    assert result["booking"]["date"] == replacement["date"]
    assert result["booking"]["time"] == replacement["time"]


def test_reschedule_rejects_unknown_booking(client, headers):
    doctors = client.get(
        "/api/appointments/doctors", headers=headers
    ).json()["doctors"]

    response = client.post(
        "/api/patient/appointments/not-a-real-booking/reschedule",
        headers=headers,
        json={
            "doctorId": doctors[0]["id"],
            "date": next_weekday().isoformat(),
            "time": "09:00",
        },
    )
    assert response.status_code == 404


def test_booking_rejects_past_dates_and_extra_fields(client, headers):
    doctors = client.get(
        "/api/appointments/doctors", headers=headers
    ).json()["doctors"]
    doctor_id = doctors[0]["id"]

    past = date.today() - timedelta(days=1)
    response = client.post(
        "/api/appointments/book",
        headers=headers,
        json={
            "doctorId": doctor_id,
            "date": past.isoformat(),
            "time": "09:00",
        },
    )
    assert response.status_code == 422

    response = client.post(
        "/api/appointments/book",
        headers=headers,
        json={
            "doctorId": doctor_id,
            "date": next_weekday().isoformat(),
            "time": "09:00",
            "patientId": "patient-002",
        },
    )
    assert response.status_code == 422


def test_booking_rejects_malformed_time(client, headers):
    doctors = client.get(
        "/api/appointments/doctors", headers=headers
    ).json()["doctors"]
    slot = available_slot(client, headers, doctors[0]["id"])

    response = client.post(
        "/api/appointments/book",
        headers=headers,
        json={
            "doctorId": doctors[0]["id"],
            "date": slot["date"],
            "time": "99:99",
            "purpose": "Malformed-time regression test",
        },
    )

    assert response.status_code == 422, response.text


def test_failed_reschedule_with_malformed_time_preserves_booking(
    client, headers
):
    doctors = client.get(
        "/api/appointments/doctors", headers=headers
    ).json()["doctors"]
    doctor_id = doctors[0]["id"]

    original_slot = available_slot(client, headers, doctor_id)
    original_booking = create_booking(
        client, headers, doctor_id, original_slot
    )

    response = client.post(
        f"/api/patient/appointments/{original_booking['bookingId']}/reschedule",
        headers=headers,
        json={
            "doctorId": doctor_id,
            "date": next_weekday(8).isoformat(),
            "time": "99:99",
        },
    )

    assert response.status_code == 422, response.text

    detail = client.get(
        f"/api/patient/appointments/{original_booking['bookingId']}",
        headers=headers,
    )
    assert detail.status_code == 200, detail.text

    booking = detail.json()["booking"]
    assert booking["status"] == "confirmed_demo"
    assert booking["date"] == original_booking["date"]
    assert booking["time"] == original_booking["time"]
