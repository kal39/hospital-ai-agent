"""Tests for privacy-safe staff analytics."""

import json
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.demo_scheduler import DemoScheduler


ANALYTICS_URL = "/api/staff/analytics"
STAFF_TOKEN = "test-only-staff-secret"


@pytest.fixture
def analytics_environment(monkeypatch):
    import app.core.auth as auth
    import app.api.analytics as analytics_api
    from app.services.appointment_requests import (
        get_appointment_request_service,
    )

    scheduler = DemoScheduler(db_path=":memory:")
    monkeypatch.setattr(analytics_api, "demo_scheduler", scheduler)

    monkeypatch.setattr(
        auth,
        "get_settings",
        lambda: SimpleNamespace(
            environment="development",
            demo_auth_enabled=True,
            demo_staff_token=STAFF_TOKEN,
        ),
    )

    # Ensure the request table exists before test data is inserted.
    get_appointment_request_service(scheduler)

    with TestClient(app) as client:
        yield client, scheduler

    scheduler._connection.close()


@pytest.fixture
def staff_headers():
    return {"X-Demo-Staff-Token": STAFF_TOKEN}


def insert_request(scheduler, request_id, status):
    scheduler._connection.execute(
        """
        INSERT INTO demo_appointment_requests (
            request_id,
            patient_id,
            status,
            submitted_at,
            updated_at,
            payload_json
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            request_id,
            "patient-001",
            status,
            "2026-11-01T10:00:00+00:00",
            "2026-11-01T10:00:00+00:00",
            json.dumps(
                {
                    "reason": "private synthetic symptom information",
                    "patientId": "patient-001",
                }
            ),
        ),
    )


def insert_booking(
    scheduler,
    booking_id,
    doctor_id,
    status,
    created_at,
):
    scheduler._connection.execute(
        """
        INSERT INTO demo_bookings (
            booking_id,
            patient_id,
            doctor_id,
            appointment_date,
            appointment_time,
            status,
            payload_json,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            booking_id,
            "patient-001",
            doctor_id,
            "2026-11-20",
            "09:30",
            status,
            json.dumps(
                {
                    "patientId": "patient-001",
                    "purpose": "private synthetic appointment reason",
                }
            ),
            created_at,
            created_at,
        ),
    )


def test_analytics_requires_staff_authentication(analytics_environment):
    client, _ = analytics_environment

    assert client.get(ANALYTICS_URL).status_code == 401

    response = client.get(
        ANALYTICS_URL,
        headers={"X-Demo-Staff-Token": "wrong-token"},
    )
    assert response.status_code == 401

    response = client.get(
        ANALYTICS_URL,
        headers={"X-Demo-Patient-Id": "patient-001"},
    )
    assert response.status_code == 401


def test_empty_analytics_returns_zero_counts(
    analytics_environment,
    staff_headers,
):
    client, _ = analytics_environment

    response = client.get(
        ANALYTICS_URL,
        headers=staff_headers,
    )

    assert response.status_code == 200, response.text

    body = response.json()

    assert body["dataSource"] == "synthetic_demo"
    assert body["dataNotice"]

    assert body["appointmentRequests"]["total"] == 0
    assert body["appointmentRequests"]["pending"] == 0
    assert body["appointmentRequests"]["confirmed"] == 0
    assert body["appointmentRequests"]["declined"] == 0
    assert body["appointmentRequests"]["cancelled"] == 0

    assert body["appointments"]["totalBooked"] == 0
    assert body["appointments"]["active"] == 0
    assert body["appointments"]["attended"] == 0
    assert body["appointments"]["missed"] == 0
    assert body["appointments"]["doctorRankings"] == []
    assert body["appointments"]["departmentRankings"] == []
    assert body["appointments"]["monthlyTrend"] == []


def test_analytics_aggregates_requests_bookings_and_attendance(
    analytics_environment,
    staff_headers,
):
    client, scheduler = analytics_environment

    request_statuses = [
        ("request-001", "submitted"),
        ("request-002", "under_review"),
        ("request-003", "appointment_offered"),
        ("request-004", "appointment_confirmed"),
        ("request-005", "declined"),
        ("request-006", "cancelled"),
    ]

    for request_id, status in request_statuses:
        insert_request(scheduler, request_id, status)

    booking_records = [
        ("booking-001", "doctor-001", "confirmed_demo"),
        ("booking-002", "doctor-001", "attended_demo"),
        ("booking-003", "doctor-005", "missed_demo"),
        ("booking-004", "doctor-003", "cancelled_demo"),
        ("booking-005", "doctor-003", "rescheduled_demo"),
    ]

    for index, (booking_id, doctor_id, status) in enumerate(
        booking_records,
        start=1,
    ):
        insert_booking(
            scheduler,
            booking_id,
            doctor_id,
            status,
            f"2026-11-{index:02d}T10:00:00+00:00",
        )

    scheduler._connection.commit()

    response = client.get(
        ANALYTICS_URL,
        headers=staff_headers,
    )

    assert response.status_code == 200, response.text

    body = response.json()

    requests = body["appointmentRequests"]
    assert requests["total"] == 6
    assert requests["pending"] == 3
    assert requests["confirmed"] == 1
    assert requests["declined"] == 1
    assert requests["cancelled"] == 1

    appointments = body["appointments"]
    assert appointments["totalBooked"] == 3
    assert appointments["active"] == 1
    assert appointments["attended"] == 1
    assert appointments["missed"] == 1

    rankings = appointments["doctorRankings"]

    assert rankings[0] == {
        "doctorId": "doctor-001",
        "doctorName": "Dr. Hana Tesfaye",
        "department": "General Medicine",
        "totalBooked": 2,
    }

    assert rankings[1]["doctorId"] == "doctor-005"
    assert rankings[1]["totalBooked"] == 1

    departments = {
        item["department"]: item["totalBooked"]
        for item in appointments["departmentRankings"]
    }

    assert departments == {
        "General Medicine": 2,
        "Cardiology": 1,
    }

    assert appointments["monthlyTrend"] == [
        {
            "month": "2026-11",
            "totalBooked": 3,
        }
    ]


def test_analytics_response_does_not_expose_patient_information(
    analytics_environment,
    staff_headers,
):
    client, scheduler = analytics_environment

    insert_request(scheduler, "private-request", "submitted")

    insert_booking(
        scheduler,
        "private-booking",
        "doctor-001",
        "confirmed_demo",
        "2026-11-01T10:00:00+00:00",
    )

    scheduler._connection.commit()

    response = client.get(
        ANALYTICS_URL,
        headers=staff_headers,
    )

    assert response.status_code == 200

    serialized = json.dumps(response.json()).casefold()

    assert "patient-001" not in serialized
    assert "private synthetic symptom information" not in serialized
    assert "private synthetic appointment reason" not in serialized
    assert "private-request" not in serialized
    assert "private-booking" not in serialized
