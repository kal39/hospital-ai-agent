"""Tests for the authenticated staff care-case workflow."""

from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.care_cases import get_care_case_service
from app.services.demo_scheduler import DemoScheduler


STAFF_URL = "/api/staff/care-cases"
PATIENT_URL = "/api/patient/care-cases"
STAFF_TOKEN = "test-only-care-case-staff-secret"


@pytest.fixture
def client(monkeypatch):
    import app.core.auth as auth
    import app.api.care_cases as care_cases_api

    scheduler = DemoScheduler(db_path=":memory:")
    monkeypatch.setattr(care_cases_api, "demo_scheduler", scheduler)

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


@pytest.fixture
def create_case(client):
    import app.api.care_cases as care_cases_api

    service = get_care_case_service(care_cases_api.demo_scheduler)
    created_ids = []

    def create(
        patient_id="patient-001",
        concern="Synthetic staff workflow test concern.",
    ):
        case = service.create_case(
            patient_id=patient_id,
            conversation_id=f"staff-test-{uuid4()}",
            reported_concern=concern,
            language="en",
            idempotency_key=f"staff-test-{uuid4()}",
        )
        created_ids.append(case["caseId"])
        return case

    yield create


def test_staff_queue_requires_staff_authentication(client):
    assert client.get(STAFF_URL).status_code == 401

    assert client.get(
        STAFF_URL,
        headers=patient_headers(),
    ).status_code == 401


def test_invalid_staff_token_is_rejected(client):
    response = client.get(
        STAFF_URL,
        headers={"X-Demo-Staff-Token": "incorrect-token"},
    )

    assert response.status_code == 401


def test_staff_can_list_cases_with_patient_ownership(client, create_case, staff_headers):
    created = create_case("patient-001")

    response = client.get(STAFF_URL, headers=staff_headers)

    assert response.status_code == 200, response.text

    body = response.json()
    assert body["dataSource"] == "synthetic_demo"

    matching = [
        case for case in body["cases"]
        if case["caseId"] == created["caseId"]
    ]

    assert len(matching) == 1
    assert matching[0]["patientId"] == "patient-001"
    assert "idempotencyKey" not in matching[0]


def test_patient_response_does_not_expose_internal_staff_fields(
    client, create_case
):
    created = create_case("patient-001")

    response = client.get(
        f"{PATIENT_URL}/{created['caseId']}",
        headers=patient_headers("patient-001"),
    )

    assert response.status_code == 200, response.text

    case = response.json()["case"]

    assert "patientId" not in case
    assert "idempotencyKey" not in case
    assert "staffActionHistory" not in case


def test_staff_can_advance_case_through_workflow(
    client, create_case, staff_headers
):
    created = create_case()
    case_id = created["caseId"]

    transitions = [
        ("acknowledged", "Staff received the case."),
        ("in_review", "Staff started reviewing the case."),
        ("resolved", "Staff completed the workflow."),
    ]

    for new_status, note in transitions:
        response = client.post(
            f"{STAFF_URL}/{case_id}/status",
            headers=staff_headers,
            json={"status": new_status, "note": note},
        )

        assert response.status_code == 200, response.text
        assert response.json()["case"]["status"] == new_status

    final_response = client.get(STAFF_URL, headers=staff_headers)
    assert final_response.status_code == 200

    final_case = next(
        item for item in final_response.json()["cases"]
        if item["caseId"] == case_id
    )

    assert final_case["status"] == "resolved"
    assert len(final_case["staffActionHistory"]) == 3


def test_internal_staff_notes_never_leak_to_patient_history(
    client, create_case, staff_headers
):
    created = create_case()
    case_id = created["caseId"]

    private_note = "INTERNAL STAFF NOTE - confidential review detail"

    staff_response = client.post(
        f"{STAFF_URL}/{case_id}/status",
        headers=staff_headers,
        json={
            "status": "acknowledged",
            "note": private_note,
        },
    )

    assert staff_response.status_code == 200, staff_response.text

    staff_case = staff_response.json()["case"]

    assert private_note in [
        item["note"] for item in staff_case["staffActionHistory"]
    ]

    patient_response = client.get(
        f"{PATIENT_URL}/{case_id}",
        headers=patient_headers(),
    )

    assert patient_response.status_code == 200, patient_response.text

    patient_case = patient_response.json()["case"]
    patient_history = patient_case["statusHistory"]

    assert private_note not in str(patient_history)
    assert all(
        item["note"] != private_note
        for item in patient_history
    )
    assert "staffActionHistory" not in patient_case


def test_invalid_workflow_transition_returns_conflict(
    client, create_case, staff_headers
):
    created = create_case()
    case_id = created["caseId"]

    response = client.post(
        f"{STAFF_URL}/{case_id}/status",
        headers=staff_headers,
        json={"status": "in_review"},
    )

    assert response.status_code == 409, response.text


def test_repeated_workflow_transition_returns_conflict(
    client, create_case, staff_headers
):
    created = create_case()
    case_id = created["caseId"]

    payload = {"status": "acknowledged"}

    first = client.post(
        f"{STAFF_URL}/{case_id}/status",
        headers=staff_headers,
        json=payload,
    )
    assert first.status_code == 200, first.text

    second = client.post(
        f"{STAFF_URL}/{case_id}/status",
        headers=staff_headers,
        json=payload,
    )

    assert second.status_code == 409, second.text


def test_unknown_case_returns_404(client, staff_headers):
    response = client.post(
        f"{STAFF_URL}/unknown-case/status",
        headers=staff_headers,
        json={"status": "acknowledged"},
    )

    assert response.status_code == 404


def test_staff_status_update_rejects_extra_fields(
    client, create_case, staff_headers
):
    created = create_case()

    response = client.post(
        f"{STAFF_URL}/{created['caseId']}/status",
        headers=staff_headers,
        json={
            "status": "acknowledged",
            "patientId": "patient-002",
        },
    )

    assert response.status_code == 422



@pytest.mark.parametrize(
    ("concern", "expected_priority"),
    [
        (
            "Severe chest pain and difficulty breathing.",
            "emergency",
        ),
        (
            "I have lower back pain and burning urination.",
            "urgent",
        ),
        (
            "I feel dizzy.",
            "urgent",
        ),
        (
            "I have a mild skin rash.",
            "routine_review",
        ),
        (
            "Should I stop taking my medication?",
            "routine_review",
        ),
    ],
)
def test_staff_priority_suggestions_follow_existing_safety_rules(
    client,
    create_case,
    staff_headers,
    concern,
    expected_priority,
):
    created = create_case(concern=concern)

    response = client.get(STAFF_URL, headers=staff_headers)

    assert response.status_code == 200, response.text

    matching = next(
        item for item in response.json()["cases"]
        if item["caseId"] == created["caseId"]
    )

    assert matching["prioritySuggestion"] == expected_priority
    assert matching["prioritySource"] == "prototype_rules"
    assert matching["priorityCreatedAt"]
    assert matching["priorityReason"]


def test_patient_response_never_exposes_priority_metadata(
    client,
    create_case,
):
    created = create_case(
        concern="Severe chest pain and difficulty breathing."
    )

    response = client.get(
        f"{PATIENT_URL}/{created['caseId']}",
        headers=patient_headers(),
    )

    assert response.status_code == 200, response.text

    case = response.json()["case"]

    assert "prioritySuggestion" not in case
    assert "priorityReason" not in case
    assert "prioritySource" not in case
    assert "priorityCreatedAt" not in case


def test_workflow_transitions_do_not_change_priority(
    client,
    create_case,
    staff_headers,
):
    created = create_case(
        concern="Severe chest pain and difficulty breathing."
    )
    case_id = created["caseId"]

    def get_staff_case():
        response = client.get(STAFF_URL, headers=staff_headers)
        assert response.status_code == 200, response.text
        return next(
            item for item in response.json()["cases"]
            if item["caseId"] == case_id
        )

    initial = get_staff_case()
    original_priority = initial["prioritySuggestion"]
    original_reason = initial["priorityReason"]

    for status in ("acknowledged", "in_review", "resolved"):
        response = client.post(
            f"{STAFF_URL}/{case_id}/status",
            headers=staff_headers,
            json={"status": status, "note": f"Test transition to {status}."},
        )

        assert response.status_code == 200, response.text

        updated = response.json()["case"]
        assert updated["status"] == status
        assert updated["prioritySuggestion"] == original_priority
        assert updated["priorityReason"] == original_reason

    final_case = get_staff_case()

    assert final_case["status"] == "resolved"
    assert final_case["prioritySuggestion"] == original_priority
    assert final_case["priorityReason"] == original_reason


def test_legacy_case_gets_staff_suggestion_without_database_rewrite(
    client,
    create_case,
    staff_headers,
):
    import json

    import app.api.care_cases as care_cases_api

    created = create_case(
        concern="I have lower back pain and burning urination."
    )
    service = get_care_case_service(care_cases_api.demo_scheduler)

    row = service._connection.execute(
        """
        SELECT payload_json
        FROM demo_care_cases
        WHERE case_id = ?
        """,
        (created["caseId"],),
    ).fetchone()

    assert row is not None

    legacy_record = json.loads(row[0])

    for field in (
        "prioritySuggestion",
        "priorityReason",
        "prioritySource",
        "priorityCreatedAt",
    ):
        legacy_record.pop(field, None)

    legacy_json = json.dumps(legacy_record)

    service._connection.execute(
        """
        UPDATE demo_care_cases
        SET payload_json = ?
        WHERE case_id = ?
        """,
        (legacy_json, created["caseId"]),
    )
    service._connection.commit()

    response = client.get(STAFF_URL, headers=staff_headers)

    assert response.status_code == 200, response.text

    staff_case = next(
        item for item in response.json()["cases"]
        if item["caseId"] == created["caseId"]
    )

    assert staff_case["prioritySuggestion"] == "urgent"
    assert staff_case["prioritySource"] == "prototype_rules"
    assert staff_case["priorityReason"]
    assert staff_case["priorityCreatedAt"] == legacy_record["createdAt"]

    persisted_row = service._connection.execute(
        """
        SELECT payload_json
        FROM demo_care_cases
        WHERE case_id = ?
        """,
        (created["caseId"],),
    ).fetchone()

    persisted_record = json.loads(persisted_row[0])

    assert persisted_record == legacy_record
    assert "prioritySuggestion" not in persisted_record
