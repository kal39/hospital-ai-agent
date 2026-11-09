
"""Tests for the hospital agent's consent-first appointment workflow."""

import asyncio

import pytest

import app.services.agent as agent_module
from app.services.agent import HospitalAgentService


@pytest.fixture(autouse=True)
def isolate_agent_state(monkeypatch):
    """Keep conversation state isolated between tests."""
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


def run_agent(
    service: HospitalAgentService,
    message: str,
    conversation_id: str = "consent-test",
    patient_id: str = "patient-001",
):
    """Run the asynchronous agent in a synchronous pytest test."""
    return asyncio.run(
        service.run(
            user_message=message,
            patient_id=patient_id,
            conversation_id=conversation_id,
            language="en",
            detail="normal",
        )
    )


def mock_llm(monkeypatch, response=None):
    """Replace the LLM call and record every invocation."""
    calls = []

    async def fake_generate_with_tools(**kwargs):
        calls.append(kwargs)
        return response or {
            "message": "Here is the requested explanation.",
            "toolsUsed": [],
        }

    monkeypatch.setattr(
        agent_module.gemini_llm_service,
        "generate_with_tools",
        fake_generate_with_tools,
    )
    return calls


def test_appointment_request_asks_consent_before_llm_or_tools(monkeypatch):
    service = HospitalAgentService()
    calls = mock_llm(monkeypatch)

    result = run_agent(
        service,
        "Can you help me find an appointment?",
    )

    assert "reply yes or no" in result["message"].lower()
    assert result["toolsUsed"] == []
    assert calls == []

    key = "patient-001:consent-test"
    assert key in agent_module._pending_appointment_requests


def test_information_question_explains_use_without_searching(monkeypatch):
    service = HospitalAgentService()
    calls = mock_llm(monkeypatch)

    first = run_agent(
        service,
        "Can you help me find an appointment?",
    )
    second = run_agent(
        service,
        "What will you do with my appointment information?",
    )

    assert first["toolsUsed"] == []
    assert "authorized hospital account" in second["message"].lower()
    assert "will not book" in second["message"].lower()
    assert "reply yes or no" in second["message"].lower()
    assert second["toolsUsed"] == []
    assert calls == []

    assert "patient-001:consent-test" in (
        agent_module._pending_appointment_requests
    )


def test_unclear_answer_keeps_consent_pending(monkeypatch):
    service = HospitalAgentService()
    calls = mock_llm(monkeypatch)

    run_agent(service, "Can you help me find an appointment?")
    result = run_agent(service, "Maybe")

    assert "reply yes" in result["message"].lower()
    assert "or no" in result["message"].lower()
    assert result["toolsUsed"] == []
    assert calls == []
    assert "patient-001:consent-test" in (
        agent_module._pending_appointment_requests
    )


def test_declining_consent_cancels_pending_request(monkeypatch):
    service = HospitalAgentService()
    calls = mock_llm(monkeypatch)

    run_agent(service, "Can you help me find an appointment?")
    result = run_agent(service, "No")

    assert "won't look for appointment options" in result["message"].lower()
    assert result["toolsUsed"] == []
    assert calls == []
    assert "patient-001:consent-test" not in (
        agent_module._pending_appointment_requests
    )


def test_explicit_yes_continues_only_after_consent(monkeypatch):
    service = HospitalAgentService()
    calls = mock_llm(
        monkeypatch,
        response={
            "message": "I can show the available demonstration options.",
            "toolsUsed": [],
        },
    )

    first = run_agent(
        service,
        "Can you help me find an appointment?",
    )

    assert first["toolsUsed"] == []
    assert calls == []

    second = run_agent(service, "Yes")

    assert len(calls) == 1
    assert "Can you help me find an appointment?" in (
        calls[0]["user_message"]
    )
    assert "explicitly consented" in calls[0]["user_message"].lower()
    assert "demo" in second["message"].lower()
    assert "synthetic" in second["message"].lower()
    assert "select" in second["message"].lower() or "number" in (
        second["message"].lower()
    )
    assert second["toolsUsed"] == ["getAvailableAppointmentSlots"]
    assert "patient-001:consent-test" not in (
        agent_module._pending_appointment_requests
    )


def test_full_explicit_appointment_consent_statement(monkeypatch):
    service = HospitalAgentService()
    calls = mock_llm(
        monkeypatch,
        response={
            "message": "I can show the available demonstration options.",
            "toolsUsed": [],
        },
    )

    run_agent(
        service,
        "Can you find available appointments for me?",
    )

    result = run_agent(
        service,
        "Yes, I consent to search for available appointments.",
    )

    assert len(calls) == 1
    assert "explicitly consented" in calls[0]["user_message"].lower()
    assert "Can you find available appointments for me?" in (
        calls[0]["user_message"]
    )
    assert "demo" in result["message"].lower()
    assert "synthetic" in result["message"].lower()
    assert "select" in result["message"].lower() or "number" in (
        result["message"].lower()
    )
    assert result["toolsUsed"] == ["getAvailableAppointmentSlots"]
    assert "patient-001:consent-test" not in (
        agent_module._pending_appointment_requests
    )


@pytest.mark.parametrize(
    "message",
    [
        "No",
        "No, I do not consent to search for appointments.",
        "I don't consent to search for appointments.",
        "No, please do not proceed.",
    ],
)
def test_explicit_refusal_never_grants_consent(monkeypatch, message):
    service = HospitalAgentService()
    calls = mock_llm(monkeypatch)

    run_agent(service, "Can you help me find an appointment?")
    result = run_agent(service, message)

    assert result["toolsUsed"] == []
    assert calls == []
    assert "patient-001:consent-test" not in (
        agent_module._pending_appointment_requests
    )


def test_ambiguous_long_answer_does_not_grant_consent(monkeypatch):
    service = HospitalAgentService()
    calls = mock_llm(monkeypatch)

    run_agent(service, "Can you help me find an appointment?")
    result = run_agent(
        service,
        "I have some questions before deciding what I want to do.",
    )

    assert result["toolsUsed"] == []
    assert calls == []
    assert "patient-001:consent-test" not in (
        agent_module._pending_appointment_requests
    )


def test_new_topic_interrupts_consent_and_is_handled_normally(monkeypatch):
    service = HospitalAgentService()
    calls = mock_llm(
        monkeypatch,
        response={
            "message": "Here is an explanation of your latest results.",
            "toolsUsed": ["getLatestLabResults"],
        },
    )

    run_agent(service, "Can you help me find an appointment?")
    result = run_agent(
        service,
        "Please explain my latest lab results.",
    )

    assert len(calls) == 1
    assert calls[0]["user_message"] == (
        "Please explain my latest lab results."
    )
    assert result["toolsUsed"] == ["getLatestLabResults"]
    assert "patient-001:consent-test" not in (
        agent_module._pending_appointment_requests
    )


def test_consent_is_not_shared_between_conversations(monkeypatch):
    service = HospitalAgentService()
    calls = mock_llm(monkeypatch)

    run_agent(
        service,
        "Can you help me find an appointment?",
        conversation_id="appointment-conversation",
    )

    result = run_agent(
        service,
        "Yes",
        conversation_id="different-conversation",
    )

    assert len(calls) == 1
    assert calls[0]["user_message"] == "Yes"
    assert result["toolsUsed"] == []

    assert (
        "patient-001:appointment-conversation"
        in agent_module._pending_appointment_requests
    )
    assert (
        "patient-001:different-conversation"
        not in agent_module._pending_appointment_requests
    )


def test_consent_is_not_shared_between_patients(monkeypatch):
    service = HospitalAgentService()
    calls = mock_llm(monkeypatch)

    run_agent(
        service,
        "Can you help me find an appointment?",
        conversation_id="shared-name",
        patient_id="patient-001",
    )

    result = run_agent(
        service,
        "Yes",
        conversation_id="shared-name",
        patient_id="patient-002",
    )

    assert len(calls) == 1
    assert calls[0]["patient_id"] == "patient-002"
    assert calls[0]["user_message"] == "Yes"
    assert result["toolsUsed"] == []

    assert (
        "patient-001:shared-name"
        in agent_module._pending_appointment_requests
    )
    assert (
        "patient-002:shared-name"
        not in agent_module._pending_appointment_requests
    )

def test_declined_request_does_not_leave_stale_llm_history(monkeypatch):
    service = HospitalAgentService()
    calls = mock_llm(monkeypatch)

    run_agent(service, "Can you help me find an appointment?")
    run_agent(service, "No, please do not proceed.")

    # A later yes must not revive the cancelled request.
    result = run_agent(service, "Yes")

    assert "patient-001:consent-test" not in (
        agent_module._pending_appointment_requests
    )
    assert len(calls) == 1
    assert calls[0]["user_message"] == "Yes"
    assert "Can you help me find an appointment?" not in (
        calls[0]["user_message"]
    )
    assert result["toolsUsed"] == []


def test_orphaned_explicit_appointment_consent_does_not_call_llm(monkeypatch):
    service = HospitalAgentService()
    calls = mock_llm(monkeypatch)

    run_agent(service, "Can you help me find an appointment?")
    run_agent(service, "No, please do not proceed.")

    result = run_agent(
        service,
        "Yes, I consent to searching for appointment options",
    )

    assert calls == []
    assert result["toolsUsed"] == []
    assert "no active appointment request" in result["message"].lower()
    assert "patient-001:consent-test" not in (
        agent_module._pending_appointment_requests
    )


def _prepare_demo_selection(monkeypatch, service, slots, patient_id="patient-001"):
    """Start a consented demo search and return its options response."""
    monkeypatch.setattr(
        agent_module,
        "_get_available_demo_options",
        lambda requested_patient_id: slots,
    )
    mock_llm(
        monkeypatch,
        response={
            "message": "I can show the available demonstration options.",
            "toolsUsed": [],
        },
    )

    first = run_agent(
        service,
        "Can you help me find an appointment?",
        patient_id=patient_id,
    )
    assert "reply yes or no" in first["message"].lower()

    return run_agent(service, "Yes", patient_id=patient_id)


def _demo_test_slots():
    return [
        {
            "doctorId": "doctor-demo-001",
            "doctorName": "Dr. Demo One",
            "department": "General Medicine",
            "date": "2099-06-10",
            "time": "09:00",
            "location": "Demo Clinic A",
            "available": True,
        },
        {
            "doctorId": "doctor-demo-002",
            "doctorName": "Dr. Demo Two",
            "department": "Cardiology",
            "date": "2099-06-11",
            "time": "10:00",
            "location": "Demo Clinic B",
            "available": True,
        },
    ]


def test_demo_booking_requires_explicit_confirmation_and_books_exact_slot(
    monkeypatch,
):
    service = HospitalAgentService()
    slots = _demo_test_slots()
    booked = []

    def fake_book_demo_appointment(**kwargs):
        booked.append(kwargs)
        return {
            "bookingId": "DEMO-TEST-001",
            "doctorId": kwargs["doctor_id"],
            "doctorName": "Dr. Demo Two",
            "department": "Cardiology",
            "location": "Demo Clinic B",
            "date": kwargs["appointment_date"],
            "time": kwargs["appointment_time"],
            "dataSource": "synthetic_demo",
        }

    monkeypatch.setattr(
        agent_module.hospital_service,
        "book_demo_appointment",
        fake_book_demo_appointment,
    )

    options_result = _prepare_demo_selection(monkeypatch, service, slots)
    assert "fictional" in options_result["message"].lower()
    assert "no appointment has been booked" in (
        options_result["message"].lower()
    )
    assert booked == []

    selection_result = run_agent(service, "2")
    assert "dr. demo two" in selection_result["message"].lower()
    assert "2099-06-11" in selection_result["message"]
    assert "10:00" in selection_result["message"]
    assert "reply yes" in selection_result["message"].lower()
    assert "nothing is booked yet" in selection_result["message"].lower()
    assert booked == []

    confirmation_result = run_agent(service, "YES")
    assert "demo booking confirmed" in (
        confirmation_result["message"].lower()
    )
    assert "DEMO-TEST-001" in confirmation_result["message"]
    assert len(booked) == 1
    assert booked[0] == {
        "patient_id": "patient-001",
        "doctor_id": "doctor-demo-002",
        "appointment_date": "2099-06-11",
        "appointment_time": "10:00",
        "purpose": "",
    }


def test_declining_demo_booking_does_not_create_booking(monkeypatch):
    service = HospitalAgentService()
    booked = []

    monkeypatch.setattr(
        agent_module.hospital_service,
        "book_demo_appointment",
        lambda **kwargs: booked.append(kwargs),
    )

    _prepare_demo_selection(monkeypatch, service, _demo_test_slots())
    run_agent(service, "2")
    result = run_agent(service, "No")

    assert "no appointment was created" in result["message"].lower()
    assert booked == []
    assert "patient-001:consent-test" not in (
        agent_module._pending_appointment_selections
    )


def test_unclear_booking_response_does_not_create_booking(monkeypatch):
    service = HospitalAgentService()
    booked = []

    monkeypatch.setattr(
        agent_module.hospital_service,
        "book_demo_appointment",
        lambda **kwargs: booked.append(kwargs),
    )

    _prepare_demo_selection(monkeypatch, service, _demo_test_slots())
    run_agent(service, "1")
    result = run_agent(service, "Maybe later")

    assert "clear yes" in result["message"].lower()
    assert "nothing has been booked yet" in result["message"].lower()
    assert booked == []
    assert agent_module._pending_appointment_selections[
        "patient-001:consent-test"
    ]["status"] == "awaiting_booking_confirmation"


def test_pending_demo_selection_is_isolated_between_patients(monkeypatch):
    service = HospitalAgentService()
    booked = []

    monkeypatch.setattr(
        agent_module.hospital_service,
        "book_demo_appointment",
        lambda **kwargs: booked.append(kwargs),
    )

    _prepare_demo_selection(monkeypatch, service, _demo_test_slots())

    patient_a_key = "patient-001:consent-test"
    assert patient_a_key in agent_module._pending_appointment_selections

    # Patient 2 uses the same conversation ID but has a different patient ID.
    other_patient_result = run_agent(
        service,
        "2",
        patient_id="patient-002",
    )

    assert "dr. demo two" not in other_patient_result["message"].lower()
    assert patient_a_key in agent_module._pending_appointment_selections

    # A YES from patient 2 must not confirm patient 1's pending selection.
    run_agent(service, "YES", patient_id="patient-002")
    assert booked == []
    assert patient_a_key in agent_module._pending_appointment_selections
def test_repeated_yes_does_not_create_a_second_demo_booking(monkeypatch):
    service = HospitalAgentService()
    booked = []

    def fake_book_demo_appointment(**kwargs):
        booked.append(kwargs)
        return {
            "bookingId": "DEMO-TEST-REPEAT-001",
            "doctorId": kwargs["doctor_id"],
            "doctorName": "Dr. Demo Two",
            "department": "Cardiology",
            "location": "Demo Clinic B",
            "date": kwargs["appointment_date"],
            "time": kwargs["appointment_time"],
            "dataSource": "synthetic_demo",
        }

    monkeypatch.setattr(
        agent_module.hospital_service,
        "book_demo_appointment",
        fake_book_demo_appointment,
    )

    _prepare_demo_selection(monkeypatch, service, _demo_test_slots())
    run_agent(service, "2")

    first_confirmation = run_agent(service, "YES")
    assert "DEMO-TEST-REPEAT-001" in first_confirmation["message"]
    assert len(booked) == 1

    repeated_confirmation = run_agent(service, "YES")
    assert "already confirmed" in repeated_confirmation["message"].lower()
    assert "DEMO-TEST-REPEAT-001" in repeated_confirmation["message"]
    assert "not created another booking" in repeated_confirmation["message"].lower()
    assert len(booked) == 1



def test_completed_demo_booking_is_isolated_between_patients(monkeypatch):
    service = HospitalAgentService()
    booked = []

    def fake_book_demo_appointment(**kwargs):
        booked.append(kwargs)
        return {
            "bookingId": "DEMO-ISOLATION-001",
            "doctorId": kwargs["doctor_id"],
            "doctorName": "Dr. Demo Two",
            "department": "Cardiology",
            "location": "Demo Clinic B",
            "date": kwargs["appointment_date"],
            "time": kwargs["appointment_time"],
            "dataSource": "synthetic_demo",
        }

    monkeypatch.setattr(
        agent_module.hospital_service,
        "book_demo_appointment",
        fake_book_demo_appointment,
    )

    _prepare_demo_selection(monkeypatch, service, _demo_test_slots())
    first_selection = run_agent(
        service, "2", patient_id="patient-001"
    )
    assert "dr. demo two" in first_selection["message"].lower()

    first_result = run_agent(
        service, "YES", patient_id="patient-001"
    )

    assert "DEMO-ISOLATION-001" in first_result["message"]
    assert len(booked) == 1

    patient_one_key = "patient-001:consent-test"
    patient_two_key = "patient-002:consent-test"

    assert patient_one_key in agent_module._completed_demo_bookings
    assert patient_two_key not in agent_module._completed_demo_bookings

    # Patient 2 must not receive Patient 1's completed booking confirmation.
    second_result = run_agent(
        service, "YES", patient_id="patient-002"
    )

    assert "DEMO-ISOLATION-001" not in second_result["message"]
    assert patient_one_key in agent_module._completed_demo_bookings
    assert patient_two_key not in agent_module._completed_demo_bookings
    assert len(booked) == 1
def test_medical_history_response_includes_synthetic_disclosure(monkeypatch):
    service = HospitalAgentService()
    mock_llm(
        monkeypatch,
        response={
            "message": (
                "Your medical history includes a routine hypertension "
                "follow-up and a medication review."
            ),
            "toolsUsed": ["getMedicalHistory"],
        },
    )

    result = run_agent(
        service,
        "Please summarize my medical history.",
    )

    message = result["message"]

    assert message.startswith("Synthetic-data notice:")
    assert "fictional demonstration records" in message
    assert "live hospital system" in message
    assert "routine hypertension follow-up" in message
    assert "medication review" in message
    assert message.count("Synthetic-data notice:") == 1
    assert result["toolsUsed"] == ["getMedicalHistory"]
