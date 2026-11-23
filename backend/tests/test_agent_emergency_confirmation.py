import asyncio
from datetime import UTC, datetime, timedelta

import pytest

import app.services.agent as agent_module
from app.services.agent import HospitalAgentService
from app.services.demo_scheduler import DemoScheduler


@pytest.fixture
def emergency_environment(monkeypatch):
    scheduler = DemoScheduler()

    monkeypatch.setattr(agent_module, "demo_scheduler", scheduler)
    monkeypatch.setattr(
        agent_module,
        "record_audit_event",
        lambda event: None,
    )

    agent_module._conversations.clear()
    agent_module._pending_emergency_confirmations.clear()
    agent_module._completed_emergency_confirmations.clear()

    yield scheduler

    agent_module._conversations.clear()
    agent_module._pending_emergency_confirmations.clear()
    agent_module._completed_emergency_confirmations.clear()
    scheduler._connection.close()


def run_agent(service, message, patient_id="patient-001",
              conversation_id="emergency-test"):
    return asyncio.run(
        service.run(
            user_message=message,
            patient_id=patient_id,
            conversation_id=conversation_id,
            language="en",
            detail="normal",
        )
    )


def pending_key(patient_id="patient-001",
                conversation_id="emergency-test"):
    return agent_module._conversation_key(patient_id, conversation_id)


def mock_llm(monkeypatch):
    calls = []

    async def fake_generate_with_tools(**kwargs):
        calls.append(kwargs)
        return {
            "message": "Normal response.",
            "toolsUsed": [],
        }

    monkeypatch.setattr(
        agent_module.gemini_llm_service,
        "generate_with_tools",
        fake_generate_with_tools,
    )
    return calls


def start_emergency(service):
    result = run_agent(
        service,
        "I have severe chest pain right now.",
    )
    assert result["safetyFlag"] is True
    assert "anyone experiencing these symptoms right now" in result["message"].lower()
    return result


def test_registration_requires_two_separate_yes_confirmations(
    emergency_environment,
):
    service = HospitalAgentService()

    start_emergency(service)

    key = pending_key()
    pending = agent_module._pending_emergency_confirmations[key]
    original_key = pending["idempotency_key"]

    first_yes = run_agent(service, "yes")

    assert "consent" in first_yes["message"].lower()
    assert "synthetic demonstration" in first_yes["message"].lower()
    assert key in agent_module._pending_emergency_confirmations
    assert (
        agent_module._pending_emergency_confirmations[key]["stage"]
        == "confirm_registration"
    )

    care_service = agent_module.get_care_case_service(
        emergency_environment
    )
    assert care_service.list_patient_cases("patient-001") == []

    second_yes = run_agent(service, "yes")

    assert second_yes["careCase"]["dataSource"] == "synthetic_demo"
    assert second_yes["careCase"]["reportedConcern"] == (
        "I have severe chest pain right now."
    )
    assert key not in agent_module._pending_emergency_confirmations

    cases = care_service.list_patient_cases("patient-001")
    assert len(cases) == 1
    assert cases[0]["caseId"] == second_yes["careCase"]["caseId"]
    assert original_key


def test_no_to_current_symptoms_does_not_register(
    emergency_environment,
):
    service = HospitalAgentService()
    start_emergency(service)

    result = run_agent(service, "no")

    assert "no case was registered" in result["message"].lower()
    assert pending_key() not in agent_module._pending_emergency_confirmations

    care_service = agent_module.get_care_case_service(
        emergency_environment
    )
    assert care_service.list_patient_cases("patient-001") == []


def test_no_to_registration_consent_does_not_register(
    emergency_environment,
):
    service = HospitalAgentService()
    start_emergency(service)

    run_agent(service, "yes")
    result = run_agent(service, "no")

    assert "no synthetic case was registered" in result["message"].lower()
    assert pending_key() not in agent_module._pending_emergency_confirmations

    care_service = agent_module.get_care_case_service(
        emergency_environment
    )
    assert care_service.list_patient_cases("patient-001") == []


def test_ambiguous_confirmation_does_not_register(
    emergency_environment,
):
    service = HospitalAgentService()
    start_emergency(service)

    result = run_agent(service, "maybe")

    assert "answer yes" in result["message"].lower()
    assert "or no" in result["message"].lower()
    assert pending_key() in agent_module._pending_emergency_confirmations

    care_service = agent_module.get_care_case_service(
        emergency_environment
    )
    assert care_service.list_patient_cases("patient-001") == []


def test_confirmation_is_patient_and_conversation_scoped(
    emergency_environment,
    monkeypatch,
):
    service = HospitalAgentService()
    calls = mock_llm(monkeypatch)

    start_emergency(service)

    run_agent(
        service,
        "yes",
        patient_id="patient-001",
        conversation_id="another-conversation",
    )

    run_agent(
        service,
        "yes",
        patient_id="patient-002",
        conversation_id="emergency-test",
    )

    assert pending_key() in agent_module._pending_emergency_confirmations
    assert len(agent_module._pending_emergency_confirmations) == 1
    assert len(calls) == 2

    care_service = agent_module.get_care_case_service(
        emergency_environment
    )
    assert care_service.list_patient_cases("patient-001") == []
    assert care_service.list_patient_cases("patient-002") == []


def test_expired_confirmation_is_discarded(
    emergency_environment,
    monkeypatch,
):
    service = HospitalAgentService()
    calls = mock_llm(monkeypatch)

    start_emergency(service)

    key = pending_key()
    agent_module._pending_emergency_confirmations[key]["expires_at"] = (
        datetime.now(UTC) - timedelta(seconds=1)
    )

    run_agent(service, "yes")

    assert key not in agent_module._pending_emergency_confirmations
    assert len(calls) == 1

    care_service = agent_module.get_care_case_service(
        emergency_environment
    )
    assert care_service.list_patient_cases("patient-001") == []


def test_database_failure_preserves_same_key_for_retry(
    emergency_environment,
    monkeypatch,
):
    service = HospitalAgentService()
    start_emergency(service)
    run_agent(service, "yes")

    key = pending_key()
    original_idempotency_key = (
        agent_module._pending_emergency_confirmations[key]["idempotency_key"]
    )

    care_service = agent_module.get_care_case_service(
        emergency_environment
    )
    original_create_case = care_service.create_case
    attempts = {"count": 0}

    def fail_once(**kwargs):
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise RuntimeError("Simulated database failure")
        return original_create_case(**kwargs)

    monkeypatch.setattr(care_service, "create_case", fail_once)

    failed = run_agent(service, "yes")

    assert "could not save" in failed["message"].lower()
    assert "no successful registration can be confirmed" in (
        failed["message"].lower()
    )
    assert key in agent_module._pending_emergency_confirmations
    assert (
        agent_module._pending_emergency_confirmations[key]["idempotency_key"]
        == original_idempotency_key
    )
    assert care_service.list_patient_cases("patient-001") == []

    retried = run_agent(service, "yes")

    assert retried["careCase"]["dataSource"] == "synthetic_demo"
    assert attempts["count"] == 2
    assert key not in agent_module._pending_emergency_confirmations
    assert len(care_service.list_patient_cases("patient-001")) == 1


def test_repeated_yes_after_registration_does_not_duplicate_case(
    emergency_environment,
):
    service = HospitalAgentService()
    start_emergency(service)

    run_agent(service, "yes")
    registered = run_agent(service, "yes")

    repeated = run_agent(service, "yes")

    assert repeated["careCase"]["caseId"] == (
        registered["careCase"]["caseId"]
    )
    assert "no second case was created" in repeated["message"].lower()

    care_service = agent_module.get_care_case_service(
        emergency_environment
    )
    assert len(care_service.list_patient_cases("patient-001")) == 1


def test_new_medical_question_interrupts_current_symptom_confirmation(
    emergency_environment,
    monkeypatch,
):
    service = HospitalAgentService()
    calls = mock_llm(monkeypatch)

    start_emergency(service)

    result = run_agent(service, "Can you explain my glucose result?")

    assert pending_key() not in agent_module._pending_emergency_confirmations
    assert len(calls) == 1
    assert "Normal response." in result["message"]

    care_service = agent_module.get_care_case_service(
        emergency_environment
    )
    assert care_service.list_patient_cases("patient-001") == []


def test_new_medical_question_interrupts_registration_consent(
    emergency_environment,
    monkeypatch,
):
    service = HospitalAgentService()
    calls = mock_llm(monkeypatch)

    start_emergency(service)
    run_agent(service, "yes")

    key = pending_key()
    assert (
        agent_module._pending_emergency_confirmations[key]["stage"]
        == "confirm_registration"
    )

    result = run_agent(service, "Can you explain my glucose result?")

    assert key not in agent_module._pending_emergency_confirmations
    assert len(calls) == 1
    assert "Normal response." in result["message"]

    care_service = agent_module.get_care_case_service(
        emergency_environment
    )
    assert care_service.list_patient_cases("patient-001") == []


def test_natural_language_registration_refusal_at_first_prompt(
    emergency_environment,
    monkeypatch,
):
    service = HospitalAgentService()
    calls = mock_llm(monkeypatch)

    start_emergency(service)

    result = run_agent(
        service,
        "No, I do not want to register a case.",
    )

    assert "no case was registered" in result["message"].lower()
    assert pending_key() not in agent_module._pending_emergency_confirmations
    assert calls == []

    care_service = agent_module.get_care_case_service(
        emergency_environment
    )
    assert care_service.list_patient_cases("patient-001") == []


@pytest.mark.parametrize(
    "message",
    [
        "How can I contact emergency services?",
        "Have you called an ambulance or notified the hospital?",
    ],
)
@pytest.mark.parametrize("stage", ["confirm_current", "confirm_registration"])
def test_emergency_information_interrupts_pending_registration(
    emergency_environment,
    monkeypatch,
    message,
    stage,
):
    service = HospitalAgentService()
    calls = mock_llm(monkeypatch)

    start_emergency(service)

    if stage == "confirm_registration":
        run_agent(service, "yes")

    key = pending_key()
    assert agent_module._pending_emergency_confirmations[key]["stage"] == stage

    result = run_agent(service, message)

    assert key not in agent_module._pending_emergency_confirmations
    assert calls == []
    assert result["toolsUsed"] == []

    answer = result["message"].lower()
    if "called an ambulance" in message.lower():
        assert "i have not called an ambulance" in answer
        assert "notified hospital staff" in answer
    else:
        assert "local emergency number" in answer
        assert "cannot place calls" in answer

    care_service = agent_module.get_care_case_service(
        emergency_environment
    )
    assert care_service.list_patient_cases("patient-001") == []


@pytest.mark.parametrize(
    ("message", "expected"),
    [
        ("\u12a0\u12ce", "yes"),
        ("\u12a0\u12ce\u1295", "yes"),
        ("\u12a0\u12ed", "no"),
        ("\u12a0\u12ed\u12f0\u1208\u121d", "no"),
        ("\u1230\u122d\u12dd", "cancel"),
        ("\u12a0\u1241\u121d", "cancel"),
    ],
)
def test_amharic_emergency_confirmation_decisions(message, expected):
    assert agent_module._emergency_confirmation_decision(message) == expected
