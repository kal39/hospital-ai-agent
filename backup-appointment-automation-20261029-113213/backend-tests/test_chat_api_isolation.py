
"""End-to-end API regression tests for chat patient isolation."""

import pytest
from fastapi.testclient import TestClient

import app.api.chat as chat_module
from app.main import app


client = TestClient(app)

CHAT_URL = "/api/chat"
DEMO_HEADER = "X-Demo-Patient-Id"
SHARED_CONVERSATION_ID = "shared-api-isolation-test"


@pytest.fixture
def agent_calls(monkeypatch):
    """Mock the agent and record the trusted arguments it receives."""
    calls = []

    async def fake_run(**kwargs):
        calls.append(kwargs)
        return {
            "message": "Synthetic test response.",
            "toolsUsed": [],
            "safetyFlag": False,
        }

    monkeypatch.setattr(
        chat_module.hospital_agent_service,
        "run",
        fake_run,
    )

    return calls


def test_chat_passes_each_authenticated_patient_to_agent(agent_calls):
    """Reusing a conversation ID must not override patient identity."""
    first_response = client.post(
        CHAT_URL,
        headers={DEMO_HEADER: "patient-001"},
        json={
            "message": "Hello from patient one.",
            "conversationId": SHARED_CONVERSATION_ID,
        },
    )

    second_response = client.post(
        CHAT_URL,
        headers={DEMO_HEADER: "patient-002"},
        json={
            "message": "Hello from patient two.",
            "conversationId": SHARED_CONVERSATION_ID,
        },
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert len(agent_calls) == 2

    # The endpoint must pass identity from the trusted dependency.
    assert agent_calls[0]["patient_id"] == "patient-001"
    assert agent_calls[1]["patient_id"] == "patient-002"

    # The shared conversation ID must not change either identity.
    assert (
        agent_calls[0]["conversation_id"]
        == SHARED_CONVERSATION_ID
    )
    assert (
        agent_calls[1]["conversation_id"]
        == SHARED_CONVERSATION_ID
    )

    assert (
        first_response.json()["conversationId"]
        == SHARED_CONVERSATION_ID
    )
    assert (
        second_response.json()["conversationId"]
        == SHARED_CONVERSATION_ID
    )


@pytest.mark.parametrize(
    "identity",
    [None, "", "patient-999"],
)
def test_chat_rejects_missing_or_invalid_identity(
    agent_calls,
    identity,
):
    """Unauthenticated requests must never reach the agent."""
    headers = {}

    if identity is not None:
        headers[DEMO_HEADER] = identity

    response = client.post(
        CHAT_URL,
        headers=headers,
        json={"message": "Show my latest laboratory results."},
    )

    assert response.status_code == 401
    assert agent_calls == []


def test_chat_rejects_client_supplied_patient_id(agent_calls):
    """The request body cannot override the authenticated identity."""
    response = client.post(
        CHAT_URL,
        headers={DEMO_HEADER: "patient-001"},
        json={
            "message": "Show my profile.",
            "patient_id": "patient-002",
        },
    )

    # ChatRequest forbids unexpected fields.
    assert response.status_code == 422

    # The invalid request must not reach the AI agent.
    assert agent_calls == []
