"""API tests for authenticated laboratory analysis."""

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)
URL = "/api/patient/labs/analysis"
DEMO_HEADER = "X-Demo-Patient-Id"


def test_patient_one_receives_structured_lab_analysis():
    response = client.get(
        URL,
        headers={DEMO_HEADER: "patient-001"},
    )

    assert response.status_code == 200
    body = response.json()

    assert body["analysisType"] == "laboratory"
    assert body["status"] == "preliminary"
    assert body["requiresClinicianReview"] is True
    assert body["dataSource"] == "synthetic_demo"
    assert "fictional" in body["dataNotice"].lower()
    assert "not a live hospital system" in body["dataNotice"].lower()

    findings = {
        finding["name"]: finding
        for finding in body["findings"]
    }

    assert findings["Hemoglobin"]["abnormality"] == "within_range"
    assert findings["Fasting Blood Glucose"]["abnormality"] == "high"
    assert findings["Creatinine"]["abnormality"] == "within_range"

    assert any(
        "synthetic/demo" in limitation
        for limitation in body["limitations"]
    )


def test_patient_two_only_receives_patient_two_lab_results():
    response = client.get(
        URL,
        headers={DEMO_HEADER: "patient-002"},
    )

    assert response.status_code == 200
    body = response.json()

    names = {finding["name"] for finding in body["findings"]}

    assert names == {"Hemoglobin", "Fasting Blood Glucose"}
    assert "Creatinine" not in names


def test_lab_analysis_rejects_missing_authentication():
    response = client.get(URL)

    assert response.status_code == 401


def test_lab_analysis_rejects_unknown_demo_patient():
    response = client.get(
        URL,
        headers={DEMO_HEADER: "patient-999"},
    )

    assert response.status_code == 401


def test_lab_analysis_does_not_require_client_supplied_patient_id():
    response = client.get(
        f"{URL}?patient_id=patient-002",
        headers={DEMO_HEADER: "patient-001"},
    )

    assert response.status_code == 200
    body = response.json()

    names = {finding["name"] for finding in body["findings"]}
    assert "Creatinine" in names
