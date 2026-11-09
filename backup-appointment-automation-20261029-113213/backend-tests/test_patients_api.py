from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

PROFILE_URL = "/api/patient/profile"
DEMO_HEADER = "X-Demo-Patient-Id"

SYNTHETIC_NOTICE_FRAGMENT = (
    "fictional local development records, not a live hospital system"
)


def test_patient_001_receives_own_profile_and_disclosure():
    response = client.get(
        PROFILE_URL,
        headers={DEMO_HEADER: "patient-001"},
    )

    assert response.status_code == 200

    body = response.json()
    patient = body["patient"]

    assert set(
        [
            "id",
            "name",
            "dateOfBirth",
            "bloodType",
            "allergies",
            "diagnoses",
            "dataSource",
            "dataNotice",
        ]
    ).issubset(patient.keys())

    assert patient["id"] == "patient-001"
    assert patient["name"] == "Abebe Kebede"
    assert patient["bloodType"] == "O+"
    assert patient["dataSource"] == "synthetic_demo"
    assert SYNTHETIC_NOTICE_FRAGMENT in patient["dataNotice"]


def test_patient_002_receives_own_profile_and_disclosure():
    response = client.get(
        PROFILE_URL,
        headers={DEMO_HEADER: "patient-002"},
    )

    assert response.status_code == 200

    patient = response.json()["patient"]

    assert patient["id"] == "patient-002"
    assert patient["name"] == "Sara Bekele"
    assert patient["bloodType"] == "A+"
    assert patient["dataSource"] == "synthetic_demo"
    assert SYNTHETIC_NOTICE_FRAGMENT in patient["dataNotice"]


def test_patient_profiles_do_not_cross_over():
    first_response = client.get(
        PROFILE_URL,
        headers={DEMO_HEADER: "patient-001"},
    )
    second_response = client.get(
        PROFILE_URL,
        headers={DEMO_HEADER: "patient-002"},
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200

    first_patient = first_response.json()["patient"]
    second_patient = second_response.json()["patient"]

    assert first_patient["id"] != second_patient["id"]
    assert first_patient["name"] == "Abebe Kebede"
    assert second_patient["name"] == "Sara Bekele"
    assert first_patient["allergies"] != second_patient["allergies"]
    assert first_patient["diagnoses"] != second_patient["diagnoses"]


def test_profile_rejects_missing_demo_identity():
    response = client.get(PROFILE_URL)

    assert response.status_code == 401


def test_profile_rejects_unknown_demo_identity():
    response = client.get(
        PROFILE_URL,
        headers={DEMO_HEADER: "patient-999"},
    )

    assert response.status_code == 401


def test_profile_rejects_empty_demo_identity():
    response = client.get(
        PROFILE_URL,
        headers={DEMO_HEADER: ""},
    )

    assert response.status_code == 401
