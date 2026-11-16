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
    agent_module._pending_appointment_selections.clear()
    agent_module._completed_demo_bookings.clear()

    monkeypatch.setattr(
        agent_module,
        "record_audit_event",
        lambda event: None,
    )

    yield

    agent_module._conversations.clear()
    agent_module._pending_appointment_requests.clear()
    agent_module._pending_appointment_selections.clear()
    agent_module._completed_demo_bookings.clear()


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
    assert "healthcare professional" in result["message"].lower()
    assert "Do not drive" in result["message"]
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
