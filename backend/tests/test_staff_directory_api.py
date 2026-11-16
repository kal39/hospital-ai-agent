"""Tests for staff-only synthetic doctor directory and availability."""

from datetime import date, timedelta
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.data.scheduling import DOCTORS
from app.services.demo_scheduler import DemoScheduler


STAFF_TOKEN = "test-only-staff-directory-secret"
DOCTORS_URL = "/api/staff/doctors"
AVAILABILITY_URL = "/api/staff/availability"


@pytest.fixture
def client(monkeypatch):
    import app.core.auth as auth
    import app.api.appointments as appointments_api

    scheduler = DemoScheduler(db_path=":memory:")
    monkeypatch.setattr(appointments_api, "demo_scheduler", scheduler)
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


def next_weekday(offset=7):
    selected = date.today() + timedelta(days=offset)

    while selected.weekday() >= 5:
        selected += timedelta(days=1)

    return selected.isoformat()


def test_staff_doctor_directory_requires_staff_authentication(client):
    assert client.get(DOCTORS_URL).status_code == 401

    response = client.get(
        DOCTORS_URL,
        headers={"X-Demo-Patient-Id": "patient-001"},
    )
    assert response.status_code == 401


def test_staff_doctor_directory_rejects_invalid_token(client):
    response = client.get(
        DOCTORS_URL,
        headers={"X-Demo-Staff-Token": "incorrect-token"},
    )
    assert response.status_code == 401


def test_staff_can_list_all_doctors(client, staff_headers):
    response = client.get(DOCTORS_URL, headers=staff_headers)

    assert response.status_code == 200, response.text
    body = response.json()

    assert len(body["doctors"]) == len(DOCTORS)
    assert body["dataSource"] == "synthetic_demo"
    assert all(
        {"id", "name", "department", "specialties", "location"}
        <= set(doctor)
        for doctor in body["doctors"]
    )


def test_staff_can_filter_doctors_by_department(client, staff_headers):
    response = client.get(
        DOCTORS_URL,
        params={"department": "general medicine"},
        headers=staff_headers,
    )

    assert response.status_code == 200, response.text
    doctors = response.json()["doctors"]

    assert len(doctors) == 2
    assert all(
        doctor["department"] == "General Medicine"
        for doctor in doctors
    )


def test_staff_doctor_filter_returns_empty_list_for_unknown_department(
    client, staff_headers
):
    response = client.get(
        DOCTORS_URL,
        params={"department": "Unknown Department"},
        headers=staff_headers,
    )

    assert response.status_code == 200
    assert response.json()["doctors"] == []


def test_staff_availability_requires_staff_authentication(client):
    response = client.get(
        AVAILABILITY_URL,
        params={
            "doctorId": "doctor-001",
            "startDate": next_weekday(),
        },
    )

    assert response.status_code == 401


def test_staff_can_list_doctor_availability(client, staff_headers):
    response = client.get(
        AVAILABILITY_URL,
        params={
            "doctorId": "doctor-001",
            "startDate": next_weekday(),
            "days": 7,
        },
        headers=staff_headers,
    )

    assert response.status_code == 200, response.text
    body = response.json()

    assert body["dataSource"] == "synthetic_demo"
    assert body["slots"]
    assert all(
        slot["doctorId"] == "doctor-001"
        and slot["doctorName"] == "Dr. Hana Tesfaye"
        and slot["department"] == "General Medicine"
        and "available" in slot
        and "slotRemainingCapacity" in slot
        for slot in body["slots"]
    )


def test_staff_availability_rejects_unknown_doctor(client, staff_headers):
    response = client.get(
        AVAILABILITY_URL,
        params={
            "doctorId": "unknown-doctor",
            "startDate": next_weekday(),
        },
        headers=staff_headers,
    )

    assert response.status_code == 422


def test_staff_availability_rejects_past_date(client, staff_headers):
    response = client.get(
        AVAILABILITY_URL,
        params={
            "doctorId": "doctor-001",
            "startDate": (date.today() - timedelta(days=1)).isoformat(),
        },
        headers=staff_headers,
    )

    assert response.status_code == 422


def test_staff_availability_rejects_days_above_limit(client, staff_headers):
    response = client.get(
        AVAILABILITY_URL,
        params={
            "doctorId": "doctor-001",
            "startDate": next_weekday(),
            "days": 31,
        },
        headers=staff_headers,
    )

    assert response.status_code == 422
