"""Integration tests for safety checks in the hospital agent workflow."""

import asyncio

import pytest

import app.services.agent as agent_module
from app.services.agent import HospitalAgentService


@pytest.fixture(autouse=True)
def isolate_agent_state(monkeypatch):
    """Isolate conversation state without mocking the real safety checker."""
    agent_module._conversations.clear()
    agent_module._pending_appointment_requests.clear()
    agent_module._pending_appointment_suggested_departments.clear()
    agent_module._pending_appointment_selections.clear()
    agent_module._completed_appointment_requests.clear()
    agent_module._pending_appointment_cancellations.clear()
    agent_module._pending_emergency_confirmations.clear()
    agent_module._completed_emergency_confirmations.clear()
    agent_module._pending_urgent_confirmations.clear()
    agent_module._completed_urgent_confirmations.clear()

    monkeypatch.setattr(
        agent_module,
        "record_audit_event",
        lambda event: None,
    )

    yield

    agent_module._conversations.clear()
    agent_module._pending_appointment_requests.clear()
    agent_module._pending_appointment_suggested_departments.clear()
    agent_module._pending_appointment_selections.clear()
    agent_module._completed_appointment_requests.clear()
    agent_module._pending_appointment_cancellations.clear()
    agent_module._pending_emergency_confirmations.clear()
    agent_module._completed_emergency_confirmations.clear()
    agent_module._pending_urgent_confirmations.clear()
    agent_module._completed_urgent_confirmations.clear()


def run_agent(service, message, language="en"):
    """Run the asynchronous agent in a synchronous pytest test."""
    return asyncio.run(
        service.run(
            user_message=message,
            patient_id="patient-001",
            conversation_id="safety-integration-test",
            language=language,
            detail="normal",
        )
    )


def mock_llm(monkeypatch):
    """Record LLM calls so blocked requests can be verified."""
    calls = []

    async def fake_generate_with_tools(**kwargs):
        calls.append(kwargs)
        return {
            "message": "Here is the requested explanation.",
            "toolsUsed": [],
        }

    monkeypatch.setattr(
        agent_module.gemini_llm_service,
        "generate_with_tools",
        fake_generate_with_tools,
    )
    return calls


def test_dizziness_is_blocked_before_llm(monkeypatch):
    service = HospitalAgentService()
    calls = mock_llm(monkeypatch)

    result = run_agent(
        service,
        "I feel dizzy after taking my medication. "
        "Should I stop taking it or change the dose?",
    )

    assert result["safetyFlag"] is True
    assert result["toolsUsed"] == []
    assert "independently" in result["message"].lower()
    assert "care team" in result["message"].lower()
    assert "Do not drive" not in result["message"]
    assert calls == []


def test_chest_pain_is_blocked_before_llm(monkeypatch):
    service = HospitalAgentService()
    calls = mock_llm(monkeypatch)

    result = run_agent(
        service,
        "I feel dizzy and have chest pain.",
    )

    assert result["safetyFlag"] is True
    assert result["toolsUsed"] == []
    assert "immediate medical attention" in result["message"].lower()
    assert calls == []


def test_normal_lab_question_can_reach_llm(monkeypatch):
    service = HospitalAgentService()
    calls = mock_llm(monkeypatch)

    result = run_agent(
        service,
        "Please explain my lab results.",
    )

    assert len(calls) == 1
    assert result["message"].startswith("Synthetic-data notice:")
    assert "Here is the requested explanation." in result["message"]
    assert result["toolsUsed"] == []
    assert result["safetyFlag"] is False

def test_dizziness_offers_urgent_registration_and_yes_creates_case(monkeypatch):
    service = HospitalAgentService()
    calls = mock_llm(monkeypatch)

    prompt = run_agent(service, "I feel dizzy.")

    key = agent_module._conversation_key(
        "patient-001",
        "safety-integration-test",
    )
    assert prompt["safetyFlag"] is True
    assert "do not drive" in prompt["message"].lower()
    assert "synthetic urgent follow-up case" in prompt["message"].lower()
    assert "reply yes" in prompt["message"].lower()
    assert key in agent_module._pending_urgent_confirmations
    assert calls == []

    registered = run_agent(service, "yes")

    assert registered["safetyFlag"] is True
    assert registered["careCase"]["caseType"] == "urgent_concern"
    assert registered["careCase"]["dataSource"] == "synthetic_demo"
    assert "not been sent to hospital staff" in registered["message"].lower()
    assert key not in agent_module._pending_urgent_confirmations
    assert key in agent_module._completed_urgent_confirmations
    assert calls == []


def test_dizziness_urgent_registration_can_be_declined(monkeypatch):
    service = HospitalAgentService()
    calls = mock_llm(monkeypatch)

    prompt = run_agent(service, "I feel dizzy.")
    key = agent_module._conversation_key(
        "patient-001",
        "safety-integration-test",
    )
    assert prompt["safetyFlag"] is True
    assert key in agent_module._pending_urgent_confirmations

    declined = run_agent(service, "no")

    assert declined["safetyFlag"] is True
    assert "no urgent follow-up case was registered" in (
        declined["message"].lower()
    )
    assert key not in agent_module._pending_urgent_confirmations
    assert "careCase" not in declined
    assert calls == []


def test_new_emergency_interrupts_pending_urgent_followup(monkeypatch):
    service = HospitalAgentService()
    calls = mock_llm(monkeypatch)

    first = run_agent(service, "I feel dizzy.")
    key = agent_module._conversation_key(
        "patient-001",
        "safety-integration-test",
    )

    assert first["safetyFlag"] is True
    assert key in agent_module._pending_urgent_confirmations

    emergency = run_agent(
        service,
        "I have severe chest pain right now.",
    )

    assert emergency["safetyFlag"] is True
    assert key not in agent_module._pending_urgent_confirmations
    assert key in agent_module._pending_emergency_confirmations
    assert agent_module._pending_emergency_confirmations[key]["stage"] == (
        "confirm_current"
    )
    assert "anyone experiencing these symptoms right now" in (
        emergency["message"].lower()
    )
    assert "careCase" not in emergency
    assert calls == []


def test_new_urgent_message_replaces_pending_emergency_confirmation(monkeypatch):
    service = HospitalAgentService()
    calls = mock_llm(monkeypatch)

    first = run_agent(service, "I feel dizzy and have chest pain.")
    key = agent_module._conversation_key(
        "patient-001",
        "safety-integration-test",
    )
    first_pending = agent_module._pending_emergency_confirmations[key]
    first_idempotency_key = first_pending["idempotency_key"]

    second = run_agent(service, "I have severe chest pain right now.")
    second_pending = agent_module._pending_emergency_confirmations[key]

    assert first["safetyFlag"] is True
    assert second["safetyFlag"] is True
    assert second_pending["stage"] == "confirm_current"
    assert second_pending["reported_concern"] == (
        "I have severe chest pain right now."
    )
    assert second_pending["idempotency_key"] != first_idempotency_key
    assert "anyone experiencing these symptoms right now" in second["message"].lower()
    assert calls == []

def test_new_emergency_interrupts_registration_consent_stage(monkeypatch):
    service = HospitalAgentService()
    calls = mock_llm(monkeypatch)

    first = run_agent(service, "I have severe chest pain right now.")

    key = agent_module._conversation_key(
        "patient-001",
        "safety-integration-test",
    )

    first_pending = agent_module._pending_emergency_confirmations[key]
    original_idempotency_key = first_pending["idempotency_key"]

    # Confirm that someone is experiencing the first emergency symptoms.
    consent_prompt = run_agent(service, "yes")

    pending_before_interrupt = (
        agent_module._pending_emergency_confirmations[key]
    )

    assert pending_before_interrupt["stage"] == "confirm_registration"
    assert "consent" in consent_prompt["message"].lower()

    # A new emergency report must not be interpreted as consent.
    new_concern = "My father suddenly collapsed and is unconscious."
    interrupted = run_agent(service, new_concern)

    replacement = agent_module._pending_emergency_confirmations[key]

    assert first["safetyFlag"] is True
    assert interrupted["safetyFlag"] is True
    assert replacement["stage"] == "confirm_current"
    assert replacement["reported_concern"] == new_concern
    assert replacement["idempotency_key"] != original_idempotency_key
    assert "anyone experiencing these symptoms right now" in (
        interrupted["message"].lower()
    )
    assert "consent" not in interrupted["message"].lower()
    assert "careCase" not in interrupted
    assert calls == []
