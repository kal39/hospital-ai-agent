"""Tests for chat-based patient appointment request management."""

import asyncio
from datetime import date, timedelta

import pytest

import app.services.agent as agent_module
from app.services.agent import HospitalAgentService
from app.services.appointment_requests import get_appointment_request_service
from app.services.demo_scheduler import DemoScheduler


@pytest.fixture(autouse=True)
def isolate_agent_state(monkeypatch):
    """Reset conversation state and disable external side effects."""
    agent_module._conversations.clear()
    agent_module._pending_appointment_requests.clear()
    agent_module._pending_appointment_selections.clear()
    agent_module._completed_appointment_requests.clear()
    agent_module._pending_appointment_cancellations.clear()

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
    agent_module._completed_appointment_requests.clear()
    agent_module._pending_appointment_cancellations.clear()


@pytest.fixture
def request_service(monkeypatch):
    """Give each test a fresh in-memory request database."""
    scheduler = DemoScheduler()
    monkeypatch.setattr(agent_module, "demo_scheduler", scheduler)

    service = get_appointment_request_service(scheduler)
    yield service

    scheduler._connection.close()


def run_agent(
    message,
    *,
    conversation_id="request-management-test",
    patient_id="patient-001",
):
    """Run the agent synchronously for a test."""
    return asyncio.run(
        HospitalAgentService().run(
            user_message=message,
            patient_id=patient_id,
            conversation_id=conversation_id,
            language="en",
            detail="normal",
        )
    )


def create_request(
    service,
    *,
    patient_id="patient-001",
    reason="Routine follow-up",
    department="Cardiology",
):
    """Create a real request record in the isolated test database."""
    preferred_date = date.today() + timedelta(days=10)

    return service.create_request(
        patient_id=patient_id,
        department=department,
        preferred_doctor="Dr. Demo One",
        preferred_date_start=preferred_date,
        preferred_date_end=preferred_date,
        reason=reason,
    )


def test_status_query_shows_only_authenticated_patients_requests(
    request_service,
):
    own_request = create_request(
        request_service,
        patient_id="patient-001",
        reason="My own request",
    )
    other_request = create_request(
        request_service,
        patient_id="patient-002",
        reason="Another patient's request",
    )

    result = run_agent(
        "Show my appointment requests",
        patient_id="patient-001",
    )

    assert own_request["requestId"] in result["message"]
    assert other_request["requestId"] not in result["message"]
    assert "synthetic demonstration data" in result["message"].lower()
    assert "not a confirmed appointment" in result["message"].lower()


def test_patient_cannot_view_another_patients_request_by_reference(
    request_service,
):
    other_request = create_request(
        request_service,
        patient_id="patient-002",
    )

    result = run_agent(
        f"Check status of appointment request {other_request['requestId']}",
        patient_id="patient-001",
    )

    assert "couldn't find" in result["message"].lower()
    assert other_request["requestId"] not in result["message"]


def test_cancellation_selection_does_not_cancel_request(
    request_service,
):
    request = create_request(request_service)

    result = run_agent("Cancel my appointment requests")

    assert request["requestId"] in result["message"]
    assert "reply with the number" in result["message"].lower()

    stored = request_service.get_patient_request(
        patient_id="patient-001",
        request_id=request["requestId"],
    )
    assert stored["status"] == "submitted"

    result = run_agent("1")

    assert "reply yes to cancel" in result["message"].lower()
    assert "no change has been made yet" in result["message"].lower()

    stored = request_service.get_patient_request(
        patient_id="patient-001",
        request_id=request["requestId"],
    )
    assert stored["status"] == "submitted"


def test_explicit_confirmation_cancels_selected_request(
    request_service,
):
    request = create_request(request_service)

    run_agent("Cancel my appointment requests")
    selection = run_agent("1")

    assert "reply yes to cancel" in selection["message"].lower()

    result = run_agent("YES")

    assert "appointment request cancelled" in result["message"].lower()
    assert request["requestId"] in result["message"]
    assert "synthetic demo only" in result["message"].lower()

    stored = request_service.get_patient_request(
        patient_id="patient-001",
        request_id=request["requestId"],
    )
    assert stored["status"] == "cancelled"

    key = "patient-001:request-management-test"
    assert key not in agent_module._pending_appointment_cancellations


def test_declining_cancellation_leaves_request_unchanged(
    request_service,
):
    request = create_request(request_service)

    run_agent("Cancel my appointment requests")
    run_agent("1")

    result = run_agent("NO")

    assert "has not been cancelled" in result["message"].lower()

    stored = request_service.get_patient_request(
        patient_id="patient-001",
        request_id=request["requestId"],
    )
    assert stored["status"] == "submitted"


def test_ambiguous_confirmation_does_not_cancel_request(
    request_service,
):
    request = create_request(request_service)

    run_agent("Cancel my appointment requests")
    run_agent("1")

    result = run_agent("Maybe")

    assert "reply yes" in result["message"].lower()
    assert "no change has been made" in result["message"].lower()

    stored = request_service.get_patient_request(
        patient_id="patient-001",
        request_id=request["requestId"],
    )
    assert stored["status"] == "submitted"

    key = "patient-001:request-management-test"
    assert (
        agent_module._pending_appointment_cancellations[key]["status"]
        == "awaiting_confirmation"
    )


def test_ambiguous_affirmative_does_not_cancel_request(
    request_service,
):
    request = create_request(request_service)

    run_agent("Cancel my appointment requests")
    run_agent("1")

    result = run_agent("sure")

    assert "reply yes" in result["message"].lower()
    assert "no change has been made" in result["message"].lower()

    stored = request_service.get_patient_request(
        patient_id="patient-001",
        request_id=request["requestId"],
    )
    assert stored["status"] == "submitted"

    key = "patient-001:request-management-test"
    assert (
        agent_module._pending_appointment_cancellations[key]["status"]
        == "awaiting_confirmation"
    )


def test_cancellation_selection_handles_request_verification_failure(
    request_service,
    monkeypatch,
):
    request = create_request(request_service)

    run_agent("Cancel my appointment requests")

    class FailingVerificationService:
        def get_patient_request(self, *, patient_id, request_id):
            raise RuntimeError("Simulated database verification failure.")

    monkeypatch.setattr(
        agent_module,
        "get_appointment_request_service",
        lambda scheduler: FailingVerificationService(),
    )

    result = run_agent("1")

    assert "temporary system problem" in result["message"].lower()
    assert "no cancellation was made" in result["message"].lower()

    stored = request_service.get_patient_request(
        patient_id="patient-001",
        request_id=request["requestId"],
    )
    assert stored["status"] == "submitted"

    key = "patient-001:request-management-test"
    assert key not in agent_module._pending_appointment_cancellations


def test_request_that_becomes_ineligible_is_not_cancelled(
    request_service,
):
    request = create_request(request_service)

    run_agent("Cancel my appointment requests")
    run_agent("1")

    # Simulate staff processing the request before patient confirmation.
    with request_service._lock:
        record = request_service._load_record(request["requestId"])
        record["status"] = "appointment_confirmed"
        request_service._save_record(record)
        request_service._connection.commit()

    result = run_agent("YES")

    assert "no longer eligible" in result["message"].lower()

    stored = request_service.get_patient_request(
        patient_id="patient-001",
        request_id=request["requestId"],
    )
    assert stored["status"] == "appointment_confirmed"


def test_cancellation_flow_cannot_select_another_patients_request(
    request_service,
):
    other_request = create_request(
        request_service,
        patient_id="patient-002",
    )

    result = run_agent(
        f"Cancel appointment request {other_request['requestId']}",
        patient_id="patient-001",
    )

    assert "couldn't find an eligible appointment request" in (
        result["message"].lower()
    )

    stored = request_service.get_patient_request(
        patient_id="patient-002",
        request_id=other_request["requestId"],
    )
    assert stored["status"] == "submitted"


def test_pending_cancellation_is_isolated_between_conversations(
    request_service,
    monkeypatch,
):
    request = create_request(request_service)

    run_agent(
        "Cancel my appointment requests",
        conversation_id="conversation-one",
    )

    key_one = "patient-001:conversation-one"
    key_two = "patient-001:conversation-two"

    assert key_one in agent_module._pending_appointment_cancellations

    async def fake_generate_with_tools(**kwargs):
        return {
            "message": "This is a separate conversation.",
            "toolsUsed": [],
        }

    monkeypatch.setattr(
        agent_module.gemini_llm_service,
        "generate_with_tools",
        fake_generate_with_tools,
    )

    result = run_agent(
        "1",
        conversation_id="conversation-two",
    )

    assert "This is a separate conversation." in result["message"]
    assert "synthetic-data notice" in result["message"].lower()
    assert key_one in agent_module._pending_appointment_cancellations
    assert key_two not in agent_module._pending_appointment_cancellations

    stored = request_service.get_patient_request(
        patient_id="patient-001",
        request_id=request["requestId"],
    )
    assert stored["status"] == "submitted"


def test_confirmed_appointment_cancellation_remains_blocked(
    request_service,
    monkeypatch,
):
    create_request(request_service)

    llm_calls = []

    async def fake_generate_with_tools(**kwargs):
        llm_calls.append(kwargs)
        return {
            "message": "Unexpected LLM response.",
            "toolsUsed": [],
        }

    monkeypatch.setattr(
        agent_module.gemini_llm_service,
        "generate_with_tools",
        fake_generate_with_tools,
    )

    result = run_agent("Cancel my appointment")

    assert "cannot book, change, or cancel a real appointment" in (
        result["message"].lower()
    )
    assert result["toolsUsed"] == []
    assert llm_calls == []


def test_status_query_handles_unexpected_request_service_failure(
    monkeypatch,
):
    class FailingRequestService:
        def list_patient_requests(self, patient_id):
            raise RuntimeError("Simulated database failure.")

    monkeypatch.setattr(
        agent_module,
        "get_appointment_request_service",
        lambda scheduler: FailingRequestService(),
    )

    result = run_agent("Show my appointment requests")

    assert "temporary system problem" in result["message"].lower()
    assert result["toolsUsed"] == []
    assert result["safetyFlag"] is False




def test_cancellation_start_handles_request_service_creation_failure(
    monkeypatch,
):
    def fail_to_create_service(scheduler):
        raise RuntimeError("Simulated database initialization failure.")

    monkeypatch.setattr(
        agent_module,
        "get_appointment_request_service",
        fail_to_create_service,
    )

    result = run_agent("Cancel my appointment request")

    assert "temporary system problem" in result["message"].lower()
    assert "no cancellation was made" in result["message"].lower()
    assert "eligible appointment request" not in result["message"].lower()
    assert result["toolsUsed"] == []
    assert result["safetyFlag"] is False
    assert (
        "request-management-test"
        not in agent_module._pending_appointment_cancellations
    )


def test_cancellation_start_handles_request_lookup_failure(
    monkeypatch,
):
    class FailingRequestService:
        def list_patient_requests(self, patient_id):
            raise RuntimeError("Simulated database query failure.")

    monkeypatch.setattr(
        agent_module,
        "get_appointment_request_service",
        lambda scheduler: FailingRequestService(),
    )

    result = run_agent("Cancel my appointment request")

    assert "temporary system problem" in result["message"].lower()
    assert "no cancellation was made" in result["message"].lower()
    assert "eligible appointment request" not in result["message"].lower()
    assert result["toolsUsed"] == []
    assert result["safetyFlag"] is False

@pytest.mark.parametrize(
    "new_message",
    [
        "I want to reschedule my appointment.",
        "Book an appointment.",
    ],
)
def test_new_appointment_action_exits_pending_cancellation_selection(
    request_service,
    new_message,
):
    request = create_request(request_service)

    run_agent("Cancel my appointment requests")

    key = "patient-001:request-management-test"
    assert key in agent_module._pending_appointment_cancellations

    result = run_agent(new_message)

    assert key not in agent_module._pending_appointment_cancellations
    assert "cannot" in result["message"].lower() or (
        "unavailable" in result["message"].lower()
    )

    stored = request_service.get_patient_request(
        patient_id="patient-001",
        request_id=request["requestId"],
    )
    assert stored["status"] == "submitted"


def test_repeated_cancellation_intent_preserves_pending_selection(
    request_service,
):
    request = create_request(request_service)

    run_agent("Cancel my appointment requests")

    key = "patient-001:request-management-test"
    assert key in agent_module._pending_appointment_cancellations

    result = run_agent("Cancel my appointment requests again")

    assert key in agent_module._pending_appointment_cancellations
    assert "select" in result["message"].lower()
    assert "nothing has been cancelled" in result["message"].lower()

    stored = request_service.get_patient_request(
        patient_id="patient-001",
        request_id=request["requestId"],
    )
    assert stored["status"] == "submitted"

