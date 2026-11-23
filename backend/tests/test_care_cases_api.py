from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.care_cases import get_care_case_service
from app.services.demo_scheduler import demo_scheduler


client = TestClient(app)
BASE_URL = "/api/patient/care-cases"
DEMO_HEADER = "X-Demo-Patient-Id"


def auth(patient_id="patient-001"):
    return {DEMO_HEADER: patient_id}


@pytest.fixture
def create_test_case():
    service = get_care_case_service(demo_scheduler)
    created_keys = []

    def create(patient_id="patient-001"):
        key = f"api-test-{uuid4()}"
        case = service.create_case(
            patient_id=patient_id,
            conversation_id=f"api-conversation-{uuid4()}",
            reported_concern="Synthetic API isolation test concern.",
            language="en",
            idempotency_key=key,
        )
        created_keys.append(key)
        return case

    yield create

    with service._lock:
        for key in created_keys:
            service._connection.execute(
                "DELETE FROM demo_care_cases WHERE idempotency_key = ?",
                (key,),
            )
        service._connection.commit()


def test_list_requires_authentication():
    response = client.get(BASE_URL)

    assert response.status_code == 401


def test_invalid_patient_authentication_is_rejected():
    response = client.get(
        BASE_URL,
        headers=auth("not-a-valid-patient"),
    )

    assert response.status_code == 401


def test_patient_can_list_own_case(create_test_case):
    created = create_test_case("patient-001")

    response = client.get(BASE_URL, headers=auth("patient-001"))

    assert response.status_code == 200
    body = response.json()
    assert body["dataSource"] == "synthetic_demo"

    cases = body["cases"]
    matching = [
        case for case in cases
        if case["caseId"] == created["caseId"]
    ]
    assert len(matching) == 1

    public_case = matching[0]
    assert "patientId" not in public_case
    assert "idempotencyKey" not in public_case


def test_patient_list_excludes_another_patients_case(create_test_case):
    patient_one_case = create_test_case("patient-001")
    patient_two_case = create_test_case("patient-002")

    response = client.get(BASE_URL, headers=auth("patient-001"))

    assert response.status_code == 200
    returned_ids = {
        case["caseId"] for case in response.json()["cases"]
    }

    assert patient_one_case["caseId"] in returned_ids
    assert patient_two_case["caseId"] not in returned_ids


def test_patient_can_retrieve_own_case(create_test_case):
    created = create_test_case("patient-001")

    response = client.get(
        f"{BASE_URL}/{created['caseId']}",
        headers=auth("patient-001"),
    )

    assert response.status_code == 200
    case = response.json()["case"]

    assert case["caseId"] == created["caseId"]
    assert case["dataSource"] == "synthetic_demo"
    assert "patientId" not in case
    assert "idempotencyKey" not in case


def test_patient_cannot_retrieve_another_patients_case(create_test_case):
    created = create_test_case("patient-001")

    response = client.get(
        f"{BASE_URL}/{created['caseId']}",
        headers=auth("patient-002"),
    )

    assert response.status_code == 404


def test_unknown_case_returns_404():
    response = client.get(
        f"{BASE_URL}/case-that-does-not-exist",
        headers=auth("patient-001"),
    )

    assert response.status_code == 404
