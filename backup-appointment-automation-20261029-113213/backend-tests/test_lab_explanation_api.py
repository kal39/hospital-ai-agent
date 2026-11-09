"""API tests for optional AI-generated laboratory explanations."""

from fastapi.testclient import TestClient

import app.api.patients as patients_module
from app.main import app
from app.schemas.clinical_analysis import LaboratoryExplanation


client = TestClient(app)
URL = "/api/patient/labs/analysis"
DEMO_HEADER = "X-Demo-Patient-Id"


def test_explanation_is_opt_in(monkeypatch):
    async def should_not_call_model(analysis):
        raise AssertionError(
            "Gemini must not be called unless includeExplanation is true."
        )

    monkeypatch.setattr(
        patients_module.gemini_llm_service,
        "generate_lab_explanation",
        should_not_call_model,
    )

    response = client.get(
        URL,
        headers={DEMO_HEADER: "patient-001"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["analysisType"] == "laboratory"
    assert "aiExplanation" not in body


def test_opt_in_returns_structured_explanation(monkeypatch):
    calls = []

    async def fake_explanation(analysis):
        calls.append(analysis)
        return LaboratoryExplanation(
            summary=(
                "Preliminary explanation of synthetic demonstration data."
            ),
            possibleExplanations=[],
            uncertaintyNotes=["Clinical context is not available."],
            questionsForClinician=[
                "Can the result be reviewed with the original report?"
            ],
            limitations=["This is not a confirmed diagnosis."],
        )

    monkeypatch.setattr(
        patients_module.gemini_llm_service,
        "generate_lab_explanation",
        fake_explanation,
    )

    response = client.get(
        URL,
        headers={DEMO_HEADER: "patient-001"},
        params={"includeExplanation": "true"},
    )

    assert response.status_code == 200
    assert len(calls) == 1
    assert calls[0].analysis_type.value == "laboratory"

    body = response.json()

    # The existing deterministic response fields remain at the top level.
    assert body["analysisType"] == "laboratory"
    assert body["requiresClinicianReview"] is True
    assert body["findings"]

    # AI explanation is an additional field only when explicitly requested.
    assert body["aiExplanation"]["summary"].startswith("Preliminary")
    assert body["aiExplanation"]["questionsForClinician"]
    assert body["aiExplanation"]["limitations"]


def test_unavailable_ai_explanation_returns_safe_503(monkeypatch):
    async def unavailable(analysis):
        raise RuntimeError("AI service is not configured.")

    monkeypatch.setattr(
        patients_module.gemini_llm_service,
        "generate_lab_explanation",
        unavailable,
    )

    response = client.get(
        URL,
        headers={DEMO_HEADER: "patient-001"},
        params={"includeExplanation": "true"},
    )

    assert response.status_code == 503
    assert "retry without includeexplanation" in response.json()["detail"].lower()
    assert "AI service is not configured" not in response.text



def test_explicit_false_does_not_call_model(monkeypatch):
    async def should_not_call_model(analysis):
        raise AssertionError(
            "Gemini must not be called when includeExplanation is false."
        )

    monkeypatch.setattr(
        patients_module.gemini_llm_service,
        "generate_lab_explanation",
        should_not_call_model,
    )

    response = client.get(
        URL,
        headers={DEMO_HEADER: "patient-001"},
        params={"includeExplanation": "false"},
    )

    assert response.status_code == 200
    assert "aiExplanation" not in response.json()


def test_unexpected_ai_failure_returns_safe_502(monkeypatch):
    async def failed_generation(analysis):
        raise RuntimeError("Internal provider details must not leak.")

    monkeypatch.setattr(
        patients_module.gemini_llm_service,
        "generate_lab_explanation",
        failed_generation,
    )

    response = client.get(
        URL,
        headers={DEMO_HEADER: "patient-001"},
        params={"includeExplanation": "true"},
    )

    assert response.status_code == 502
    assert response.json()["detail"] == (
        "The AI lab explanation could not be generated."
    )
    assert "Internal provider details" not in response.text
