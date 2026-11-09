"""API tests for the synthetic appointment request workflow."""

from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)
BASE_URL = "/api/patient/appointment-requests"
DEMO_HEADER = "X-Demo-Patient-Id"


def auth(patient_id: str = "patient-001") -> dict[str, str]:
    return {DEMO_HEADER: patient_id}


def submit_request(
    patient_id: str = "patient-001",
    **overrides,
):
    payload = {
        "department": "General Medicine",
        "preferredDoctor": "Dr. Demo",
        "preferredDateStart": (date.today() + timedelta(days=7)).isoformat(),
        "preferredDateEnd": (date.today() + timedelta(days=14)).isoformat(),
        "reason": "I would like to request an additional follow-up visit.",
    }
    payload.update(overrides)
    return client.post(BASE_URL, headers=auth(patient_id), json=payload)


def test_patient_can_submit_request():
    response = submit_request()

    assert response.status_code == 201
    request = response.json()["request"]

    assert request["status"] == "submitted"
    assert request["dataSource"] == "synthetic_demo"
    assert request["requestId"].startswith("demo-req-")
    assert request["statusHistory"][0]["status"] == "submitted"
    assert "patientId" not in request
    assert "not been sent to a real hospital" in request["dataNotice"]


def test_patient_can_list_own_requests():
    created = submit_request()
    assert created.status_code == 201
    request_id = created.json()["request"]["requestId"]

    response = client.get(BASE_URL, headers=auth("patient-001"))

    assert response.status_code == 200
    ids = [item["requestId"] for item in response.json()["requests"]]
    assert request_id in ids


def test_other_patient_cannot_read_request():
    created = submit_request("patient-001")
    request_id = created.json()["request"]["requestId"]

    response = client.get(
        f"{BASE_URL}/{request_id}",
        headers=auth("patient-002"),
    )

    assert response.status_code == 404


def test_other_patient_cannot_cancel_request():
    created = submit_request("patient-001")
    request_id = created.json()["request"]["requestId"]

    response = client.post(
        f"{BASE_URL}/{request_id}/cancel",
        headers=auth("patient-002"),
    )

    assert response.status_code == 404

    # The owning patient can still retrieve the request unchanged.
    own_response = client.get(
        f"{BASE_URL}/{request_id}",
        headers=auth("patient-001"),
    )
    assert own_response.status_code == 200
    assert own_response.json()["request"]["status"] == "submitted"


def test_patient_can_cancel_own_submitted_request():
    created = submit_request()
    request_id = created.json()["request"]["requestId"]

    response = client.post(
        f"{BASE_URL}/{request_id}/cancel",
        headers=auth("patient-001"),
    )

    assert response.status_code == 200
    request = response.json()["request"]
    assert request["status"] == "cancelled"
    assert request["statusHistory"][-1]["status"] == "cancelled"


def test_cancelled_request_cannot_be_cancelled_again():
    created = submit_request()
    request_id = created.json()["request"]["requestId"]

    first = client.post(
        f"{BASE_URL}/{request_id}/cancel",
        headers=auth("patient-001"),
    )
    second = client.post(
        f"{BASE_URL}/{request_id}/cancel",
        headers=auth("patient-001"),
    )

    assert first.status_code == 200
    assert second.status_code == 409


def test_request_rejects_client_supplied_patient_id():
    response = client.post(
        BASE_URL,
        headers=auth("patient-001"),
        json={
            "patient_id": "patient-002",
            "reason": "I need an additional follow-up visit.",
        },
    )

    assert response.status_code == 422


def test_request_rejects_short_reason():
    response = submit_request(reason="Help")

    assert response.status_code == 422


def test_request_rejects_past_preferred_date():
    past_date = (date.today() - timedelta(days=1)).isoformat()

    response = submit_request(
        preferredDateStart=past_date,
        preferredDateEnd=past_date,
    )

    assert response.status_code == 422


def test_request_rejects_end_date_before_start_date():
    start = (date.today() + timedelta(days=14)).isoformat()
    end = (date.today() + timedelta(days=7)).isoformat()

    response = submit_request(
        preferredDateStart=start,
        preferredDateEnd=end,
    )

    assert response.status_code == 422


@pytest.mark.parametrize(
    "headers",
    [{}, {DEMO_HEADER: "patient-999"}],
)
def test_request_requires_valid_demo_identity(headers):
    response = client.get(BASE_URL, headers=headers)

    assert response.status_code == 401


def test_patient_request_list_does_not_include_other_patient_requests():
    first = submit_request("patient-001")
    second = submit_request("patient-002")

    assert first.status_code == 201
    assert second.status_code == 201

    first_id = first.json()["request"]["requestId"]
    second_id = second.json()["request"]["requestId"]

    response = client.get(BASE_URL, headers=auth("patient-001"))
    assert response.status_code == 200

    ids = [item["requestId"] for item in response.json()["requests"]]
    assert first_id in ids
    assert second_id not in ids
