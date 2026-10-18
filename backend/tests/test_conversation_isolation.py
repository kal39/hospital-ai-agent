"""Regression tests for patient-specific LLM conversation history."""

import asyncio

import pytest

import app.services.agent as agent_module
from app.services.agent import HospitalAgentService


@pytest.fixture(autouse=True)
def isolate_agent_state(monkeypatch):
    """Keep conversation and appointment state isolated between tests."""
    agent_module._conversations.clear()
    agent_module._pending_appointment_requests.clear()
    agent_module._pending_appointment_selections.clear()
    agent_module._completed_demo_bookings.clear()

    monkeypatch.setattr(
        agent_module,
        "evaluate_safety",
        lambda message, language: {
            "blocked": False,
            "urgent": False,
            "message": None,
        },
    )
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


def test_llm_conversation_history_is_isolated_between_patients(monkeypatch):
    """Patients using the same conversation ID must not share history."""
    service = HospitalAgentService()
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

    shared_conversation_id = "shared-history-test"
    private_marker = "BLUE-ORCHID-781"

    async def exercise_conversations():
        # Patient 1 establishes a conversation containing a unique marker.
        await service.run(
            user_message=f"Please remember this test phrase: {private_marker}",
            patient_id="patient-001",
            conversation_id=shared_conversation_id,
            language="en",
            detail="normal",
        )

        # Patient 1's next turn should receive their own previous history.
        await service.run(
            user_message="What phrase did I ask you to remember?",
            patient_id="patient-001",
            conversation_id=shared_conversation_id,
            language="en",
            detail="normal",
        )

        # Patient 2 reuses the same conversation ID.
        await service.run(
            user_message="What have we discussed so far?",
            patient_id="patient-002",
            conversation_id=shared_conversation_id,
            language="en",
            detail="normal",
        )

    asyncio.run(exercise_conversations())

    assert len(calls) == 3

    patient_1_history = calls[1]["conversation_history"]
    patient_2_history = calls[2]["conversation_history"]

    # Patient 1's history contains their own previous message.
    assert any(
        private_marker in item["content"]
        for item in patient_1_history
    )

    # Patient 2 must not receive Patient 1's private message or response.
    assert all(
        private_marker not in item["content"]
        for item in patient_2_history
    )

    # Patient 2 starts with a separate, empty conversation history.
    assert patient_2_history == []
