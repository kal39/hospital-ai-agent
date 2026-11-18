
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
    agent_module._pending_appointment_suggested_departments.clear()
    agent_module._pending_appointment_departments.clear()
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
    agent_module._pending_appointment_suggested_departments.clear()
    agent_module._pending_appointment_departments.clear()
    agent_module._pending_appointment_selections.clear()
    agent_module._completed_appointment_requests.clear()
    agent_module._pending_appointment_cancellations.clear()



@pytest.mark.parametrize(
    "message",
    [
        "I want to see Obstetrics and Gynecology.",
        "I want to see Obstetrics & Gynecology.",
        "I want to see OB-GYN.",
        "I want to see OBGYN.",
    ],
)
def test_gynecology_aliases_resolve_to_canonical_department(message):
    assert agent_module._extract_requested_department(message) == "Gynecology"


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
    assert second["toolsUsed"] == ["findAppropriateDoctors"]
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
    assert result["toolsUsed"] == ["findAppropriateDoctors"]
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
    """Start a consented demo search and return doctor recommendations."""
    doctors_by_id = {}

    for slot in slots:
        doctor_id = slot["doctorId"]
        doctors_by_id.setdefault(doctor_id, {
            "id": doctor_id,
            "name": slot["doctorName"],
            "department": slot["department"],
            "specialties": [],
            "location": slot.get("location", ""),
            "isAssignedDoctor": False,
            "dataSource": "synthetic_demo",
            "dataNotice": "Synthetic demo data only",
        })

    doctors = list(doctors_by_id.values())

    monkeypatch.setattr(
        agent_module, "_get_demo_doctors",
        lambda requested_patient_id, department="": [
            doctor
            for doctor in doctors
            if not department
            or doctor.get("department", "").casefold() == department.casefold()
        ],
    )
    monkeypatch.setattr(
        agent_module, "_get_available_slots_for_doctor",
        lambda requested_patient_id, doctor_id: [
            slot for slot in slots if slot["doctorId"] == doctor_id
        ],
    )
    mock_llm(monkeypatch, response={
        "message": "I can show the available demonstration options.",
        "toolsUsed": [],
    })

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


def _fake_request_service(requests, failure=None):
    """Build a fake request service that records submitted request data."""

    class FakeRequestService:
        def create_request(self, **kwargs):
            requests.append(kwargs)

            if failure is not None:
                raise failure

            preferred_date = kwargs["preferred_date_start"].isoformat()

            return {
                "requestId": f"DEMO-REQUEST-{len(requests):03d}",
                "status": "submitted",
                "department": kwargs["department"],
                "preferredDoctor": kwargs["preferred_doctor"],
                "preferredDateStart": preferred_date,
                "preferredDateEnd": kwargs["preferred_date_end"].isoformat(),
                "dataSource": "synthetic_demo",
                "dataNotice": "Synthetic demo data only",
            }

    return FakeRequestService()


def test_doctor_can_be_selected_by_exact_displayed_name(monkeypatch):
    service = HospitalAgentService()
    _prepare_demo_selection(monkeypatch, service, _demo_test_slots())

    result = run_agent(service, "Dr. Demo Two")

    assert "dr. demo two" in result["message"].lower()
    assert any(
        slot.get("date") == "2099-06-11"
        and slot.get("time") == "10:00"
        for slot in result.get("appointmentSlots", [])
    )
    assert "choose a date from the calendar" in result["message"].lower()
    assert "select an available time" in result["message"].lower()


def test_doctor_name_selection_is_case_and_punctuation_insensitive(monkeypatch):
    service = HospitalAgentService()
    _prepare_demo_selection(monkeypatch, service, _demo_test_slots())

    result = run_agent(service, "DR demo TWO")

    assert "dr. demo two" in result["message"].lower()
    assert any(
        slot.get("date") == "2099-06-11"
        and slot.get("time") == "10:00"
        for slot in result.get("appointmentSlots", [])
    )


def test_unique_short_doctor_name_can_be_selected(monkeypatch):
    service = HospitalAgentService()
    _prepare_demo_selection(monkeypatch, service, _demo_test_slots())

    result = run_agent(service, "Demo Two")

    assert "dr. demo two" in result["message"].lower()
    assert any(
        slot.get("date") == "2099-06-11"
        and slot.get("time") == "10:00"
        for slot in result.get("appointmentSlots", [])
    )


def test_ambiguous_doctor_name_does_not_select_a_doctor(monkeypatch):
    service = HospitalAgentService()
    slots = [
        {
            **_demo_test_slots()[0],
            "doctorName": "Dr. Hana Tesfaye",
        },
        {
            **_demo_test_slots()[1],
            "doctorName": "Dr. Hana Bekele",
        },
    ]
    _prepare_demo_selection(monkeypatch, service, slots)

    result = run_agent(service, "Hana")

    assert "choose one of the displayed doctors" in result["message"].lower()
    assert "no request has been submitted" in result["message"].lower()
    assert agent_module._pending_appointment_selections[
        "patient-001:consent-test"
    ]["status"] == "awaiting_doctor_selection"


def test_appointment_request_requires_explicit_confirmation_and_preserves_details(
    monkeypatch,
):
    service = HospitalAgentService()
    slots = _demo_test_slots()
    submitted = []
    fake_service = _fake_request_service(submitted)

    monkeypatch.setattr(
        agent_module,
        "get_appointment_request_service",
        lambda scheduler: fake_service,
    )

    options_result = _prepare_demo_selection(monkeypatch, service, slots)

    assert "fictional" in options_result["message"].lower()
    assert "no appointment request has been submitted" in (
        options_result["message"].lower()
    )
    assert submitted == []

    assert [doctor["id"] for doctor in options_result["doctorRecommendations"]] == [
        "doctor-demo-001", "doctor-demo-002"
    ]

    doctor_selection_result = run_agent(service, "2")
    assert "dr. demo two" in doctor_selection_result["message"].lower()
    assert any(
        slot.get("date") == "2099-06-11"
        and slot.get("time") == "10:00"
        for slot in doctor_selection_result.get("appointmentSlots", [])
    )
    assert "choose a date from the calendar" in doctor_selection_result["message"].lower()
    assert "select an available time" in doctor_selection_result["message"].lower()
    assert submitted == []

    slot_selection_result = run_agent(service, "1")
    assert "dr. demo two" in slot_selection_result["message"].lower()
    assert "2099-06-11" in slot_selection_result["message"]
    assert "10:00" in slot_selection_result["message"]
    assert "reply yes" in slot_selection_result["message"].lower()
    assert "no request has been submitted yet" in (
        slot_selection_result["message"].lower()
    )
    assert submitted == []

    confirmation_result = run_agent(service, "YES")

    assert "appointment request submitted" in (
        confirmation_result["message"].lower()
    )
    assert "DEMO-REQUEST-001" in confirmation_result["message"]
    assert "pending staff review" in confirmation_result["message"].lower()
    assert "not a confirmed appointment" in (
        confirmation_result["message"].lower()
    )
    assert "not been reserved" in confirmation_result["message"].lower()

    assert len(submitted) == 1
    assert submitted[0]["patient_id"] == "patient-001"
    assert submitted[0]["department"] == "Cardiology"
    assert submitted[0]["preferred_doctor"] == "Dr. Demo Two"
    assert submitted[0]["preferred_date_start"].isoformat() == "2099-06-11"
    assert submitted[0]["preferred_date_end"].isoformat() == "2099-06-11"
    assert submitted[0]["reason"] == "Can you help me find an appointment?"


@pytest.mark.parametrize(
    "exception_type",
    [ValueError, RuntimeError],
)
def test_appointment_request_submission_failures_are_safe_and_clear_pending_state(
    monkeypatch,
    exception_type,
):
    service = HospitalAgentService()
    submitted = []
    internal_message = "INTERNAL-SECRET-DETAIL-DO-NOT-EXPOSE"
    fake_service = _fake_request_service(
        submitted,
        failure=exception_type(internal_message),
    )
    audit_events = []

    monkeypatch.setattr(
        agent_module,
        "get_appointment_request_service",
        lambda scheduler: fake_service,
    )
    monkeypatch.setattr(
        agent_module,
        "record_audit_event",
        lambda event: audit_events.append(event),
    )

    _prepare_demo_selection(monkeypatch, service, _demo_test_slots())
    run_agent(service, "2")
    run_agent(service, "1")

    key = "patient-001:consent-test"
    assert key in agent_module._pending_appointment_selections

    result = run_agent(service, "YES")

    assert internal_message not in result["message"]
    assert "no appointment" in result["message"].lower()
    assert key not in agent_module._completed_appointment_requests
    assert len(submitted) == 1

    if exception_type is ValueError:
        # Validation failures must clear the pending confirmation.
        assert "couldn't submit" in result["message"].lower()
        assert key not in agent_module._pending_appointment_selections
    else:
        # Unexpected failures retain the confirmation for safe retry.
        assert "couldn't verify" in result["message"].lower()
        assert "reply yes" in result["message"].lower()
        assert key in agent_module._pending_appointment_selections

        pending = agent_module._pending_appointment_selections[key]
        assert pending["status"] == "awaiting_request_confirmation"
        assert pending.get("idempotency_key")

    failure_event = next(
        event
        for event in audit_events
        if event.get("event") == "AI_APPOINTMENT_REQUEST_FAILED"
    )
    assert failure_event["details"]["reason"] in {
        "validation_failed",
        "submission_error",
    }
    assert internal_message not in str(failure_event)


def test_declining_appointment_request_does_not_submit_request(monkeypatch):
    service = HospitalAgentService()
    submitted = []
    fake_service = _fake_request_service(submitted)

    monkeypatch.setattr(
        agent_module,
        "get_appointment_request_service",
        lambda scheduler: fake_service,
    )

    _prepare_demo_selection(monkeypatch, service, _demo_test_slots())
    run_agent(service, "2")
    run_agent(service, "1")
    result = run_agent(service, "No")

    assert "cancelled before submission" in result["message"].lower()
    assert "no request was submitted" in result["message"].lower()
    assert submitted == []
    assert "patient-001:consent-test" not in (
        agent_module._pending_appointment_selections
    )


def test_unclear_request_confirmation_does_not_submit_request(monkeypatch):
    service = HospitalAgentService()
    submitted = []
    fake_service = _fake_request_service(submitted)

    monkeypatch.setattr(
        agent_module,
        "get_appointment_request_service",
        lambda scheduler: fake_service,
    )

    _prepare_demo_selection(monkeypatch, service, _demo_test_slots())
    run_agent(service, "1")
    run_agent(service, "1")
    result = run_agent(service, "Maybe later")

    assert "clear yes" in result["message"].lower()
    assert "nothing has been submitted" in result["message"].lower()
    assert submitted == []
    assert agent_module._pending_appointment_selections[
        "patient-001:consent-test"
    ]["status"] == "awaiting_request_confirmation"


def test_pending_appointment_request_selection_is_isolated_between_patients(
    monkeypatch,
):
    service = HospitalAgentService()
    submitted = []
    fake_service = _fake_request_service(submitted)

    monkeypatch.setattr(
        agent_module,
        "get_appointment_request_service",
        lambda scheduler: fake_service,
    )

    _prepare_demo_selection(monkeypatch, service, _demo_test_slots())

    patient_a_key = "patient-001:consent-test"
    assert patient_a_key in agent_module._pending_appointment_selections

    other_patient_result = run_agent(
        service,
        "2",
        patient_id="patient-002",
    )

    assert "dr. demo two" not in other_patient_result["message"].lower()
    assert patient_a_key in agent_module._pending_appointment_selections

    run_agent(service, "YES", patient_id="patient-002")

    assert submitted == []
    assert patient_a_key in agent_module._pending_appointment_selections


def test_repeated_yes_does_not_submit_a_second_appointment_request(monkeypatch):
    service = HospitalAgentService()
    submitted = []
    fake_service = _fake_request_service(submitted)

    monkeypatch.setattr(
        agent_module,
        "get_appointment_request_service",
        lambda scheduler: fake_service,
    )

    _prepare_demo_selection(monkeypatch, service, _demo_test_slots())
    run_agent(service, "2")
    run_agent(service, "1")

    first_confirmation = run_agent(service, "YES")

    assert "DEMO-REQUEST-001" in first_confirmation["message"]
    assert len(submitted) == 1

    repeated_confirmation = run_agent(service, "YES")

    assert "already submitted" in repeated_confirmation["message"].lower()
    assert "DEMO-REQUEST-001" in repeated_confirmation["message"]
    assert "not submitted another request" in (
        repeated_confirmation["message"].lower()
    )
    assert len(submitted) == 1


def test_completed_appointment_request_is_isolated_between_patients(
    monkeypatch,
):
    service = HospitalAgentService()
    submitted = []
    fake_service = _fake_request_service(submitted)

    monkeypatch.setattr(
        agent_module,
        "get_appointment_request_service",
        lambda scheduler: fake_service,
    )

    _prepare_demo_selection(monkeypatch, service, _demo_test_slots())

    first_selection = run_agent(
        service,
        "2",
        patient_id="patient-001",
    )
    assert "dr. demo two" in first_selection["message"].lower()

    slot_selection = run_agent(
        service,
        "1",
        patient_id="patient-001",
    )
    assert "2099-06-11" in slot_selection["message"]

    first_result = run_agent(
        service,
        "YES",
        patient_id="patient-001",
    )

    assert "DEMO-REQUEST-001" in first_result["message"]
    assert len(submitted) == 1

    patient_one_key = "patient-001:consent-test"
    patient_two_key = "patient-002:consent-test"

    assert patient_one_key in agent_module._completed_appointment_requests
    assert patient_two_key not in agent_module._completed_appointment_requests

    second_result = run_agent(
        service,
        "YES",
        patient_id="patient-002",
    )

    assert "DEMO-REQUEST-001" not in second_result["message"]
    assert patient_one_key in agent_module._completed_appointment_requests
    assert patient_two_key not in agent_module._completed_appointment_requests
    assert len(submitted) == 1



def test_symptom_request_for_department_and_available_doctors_asks_consent(
    monkeypatch,
):
    service = HospitalAgentService()
    calls = mock_llm(monkeypatch)

    result = run_agent(
        service,
        "I've had a persistent cough for five days. "
        "Can you help me find the appropriate department and available doctors?",
    )

    key = "patient-001:consent-test"
    assert result["toolsUsed"] == []
    assert calls == []
    assert key in agent_module._pending_appointment_requests


def test_department_preference_does_not_grant_consent_or_query_directory(
    monkeypatch,
):
    service = HospitalAgentService()
    calls = mock_llm(monkeypatch)
    directory_calls = []
    original_lookup = (
        agent_module.hospital_service.find_appropriate_doctors
    )

    def tracked_lookup(patient_id, department=""):
        directory_calls.append((patient_id, department))
        return original_lookup(patient_id, department=department)

    monkeypatch.setattr(
        agent_module.hospital_service,
        "find_appropriate_doctors",
        tracked_lookup,
    )

    first = run_agent(
        service,
        "I've had a persistent cough for five days. "
        "Can you help me find the appropriate department and available doctors?",
    )
    second = run_agent(service, "ok respiratory clinic")

    key = "patient-001:consent-test"
    assert first["toolsUsed"] == []
    assert second["toolsUsed"] == []
    assert calls == []
    assert directory_calls == []
    assert key in agent_module._pending_appointment_requests
    assert agent_module._pending_appointment_departments[key] == (
        "Respiratory Clinic"
    )
    assert "respiratory clinic" in second["message"].lower()
    assert "yes or no" in second["message"].lower()


def test_department_filter_is_applied_only_after_explicit_yes(monkeypatch):
    service = HospitalAgentService()
    calls = mock_llm(
        monkeypatch,
        response={
            "message": "I can show the available demonstration options.",
            "toolsUsed": [],
        },
    )
    directory_calls = []
    original_lookup = (
        agent_module.hospital_service.find_appropriate_doctors
    )

    def tracked_lookup(patient_id, department=""):
        directory_calls.append((patient_id, department))
        return original_lookup(patient_id, department=department)

    monkeypatch.setattr(
        agent_module.hospital_service,
        "find_appropriate_doctors",
        tracked_lookup,
    )

    run_agent(
        service,
        "I've had a persistent cough for five days. "
        "Can you help me find the appropriate department and available doctors?",
    )
    preference = run_agent(service, "ok respiratory clinic")

    assert preference["toolsUsed"] == []
    assert directory_calls == []

    result = run_agent(service, "yes")

    key = "patient-001:consent-test"
    assert len(calls) == 1
    assert directory_calls == [("patient-001", "Respiratory Clinic")]
    assert result["toolsUsed"] == ["findAppropriateDoctors"]
    assert result["doctorRecommendations"]
    assert all(
        doctor["department"] == "Respiratory Clinic"
        for doctor in result["doctorRecommendations"]
    )
    assert "general medicine" not in result["message"].lower()
    assert "respiratory clinic" in result["message"].lower()
    assert key not in agent_module._pending_appointment_requests
    assert key not in agent_module._pending_appointment_departments


def test_natural_yes_accepts_department_filter_but_still_requires_search_consent(
    monkeypatch,
):
    service = HospitalAgentService()
    calls = mock_llm(
        monkeypatch,
        response={
            "message": "I can show the available demonstration doctors.",
            "toolsUsed": [],
        },
    )
    directory_calls = []
    original_lookup = (
        agent_module.hospital_service.find_appropriate_doctors
    )

    def tracked_lookup(patient_id, department=""):
        directory_calls.append((patient_id, department))
        return original_lookup(patient_id, department=department)

    monkeypatch.setattr(
        agent_module.hospital_service,
        "find_appropriate_doctors",
        tracked_lookup,
    )

    first = run_agent(
        service,
        "I've had a persistent cough for five days. "
        "Can you help me find the appropriate department and available doctors?",
    )

    # This accepts the suggested filter only. It must not search the directory.
    second = run_agent(
        service,
        "Yes, please help me find an available doctor.",
    )

    key = "patient-001:consent-test"
    assert first["toolsUsed"] == []
    assert second["toolsUsed"] == []
    assert calls == []
    assert directory_calls == []
    assert key in agent_module._pending_appointment_requests
    assert agent_module._pending_appointment_departments[key] == (
        "Respiratory Clinic"
    )
    assert "yes or no" in second["message"].lower()
    assert "search the demonstration doctor directory" in second["message"].lower()

    # Only the separate, explicit consent reply may trigger directory discovery.
    third = run_agent(
        service,
        "Yes, I consent to searching for available doctors and appointment times.",
    )

    assert len(calls) == 1
    assert directory_calls == [("patient-001", "Respiratory Clinic")]
    assert third["toolsUsed"] == ["findAppropriateDoctors"]
    assert third["doctorRecommendations"]
    assert all(
        doctor["department"] == "Respiratory Clinic"
        for doctor in third["doctorRecommendations"]
    )
    assert key not in agent_module._pending_appointment_requests
    assert key not in agent_module._pending_appointment_departments


def test_workflow_detector_matches_department_and_doctor_discovery_request():
    assert agent_module._is_appointment_workflow_request(
        "I've had a persistent cough for five days. "
        "Can you help me find the appropriate department and available doctors?"
    )
    assert agent_module._is_appointment_workflow_request(
        "I need appointment for persistent cough and breathing issue"
    )
    assert agent_module._is_appointment_workflow_request(
        "I would like an appointment"
    )
    assert not agent_module._is_appointment_workflow_request(
        "I have a cough. What could be causing it?"
    )


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


def test_model_generated_consent_uses_tentative_symptom_department_filter(
    monkeypatch,
):
    service = HospitalAgentService()
    calls = mock_llm(
        monkeypatch,
        response={
            "message": (
                "Would you like help checking available appointment options?"
            ),
            "toolsUsed": [],
        },
    )

    symptom = (
        "My heartbeat feels irregular, and sometimes my heart starts racing."
    )
    first = run_agent(service, symptom)

    key = "patient-001:consent-test"

    assert first["toolsUsed"] == []
    assert "cardiology" in first["message"].lower()
    assert "preferred directory filter" in first["message"].lower()
    assert "separately" in first["message"].lower()
    assert len(calls) == 1
    assert agent_module._pending_appointment_requests[key] == symptom
    assert (
        agent_module._pending_appointment_suggested_departments[key]
        == "Cardiology"
    )

    # First yes accepts only the suggested filter, not directory discovery.
    second = run_agent(service, "Yes")

    assert second["toolsUsed"] == []
    assert "cardiology" in second["message"].lower()
    assert "read-only" in second["message"].lower()
    assert "reply yes or no" in second["message"].lower()
    assert len(calls) == 1
    assert key in agent_module._pending_appointment_requests
    assert key not in agent_module._pending_appointment_suggested_departments
    assert agent_module._pending_appointment_departments[key] == "Cardiology"

    # The second yes grants read-only discovery and returns only Cardiology.
    third = run_agent(service, "Yes")

    assert third["toolsUsed"] == ["findAppropriateDoctors"]
    assert third.get("doctorRecommendations")
    assert all(
        doctor["department"] == "Cardiology"
        for doctor in third["doctorRecommendations"]
    )
    assert len(calls) == 2
    assert key not in agent_module._pending_appointment_requests


def test_model_generated_consent_uses_general_medicine_fallback_for_explicit_department_question(
    monkeypatch,
):
    service = HospitalAgentService()
    calls = mock_llm(
        monkeypatch,
        response={
            "message": (
                "Would you like help checking available appointment options?"
            ),
            "toolsUsed": [],
        },
    )

    symptom = (
        "I have been experiencing frequent headaches. "
        "Which department should I visit?"
    )
    key = "patient-001:consent-test"

    # First turn: suggest General Medicine as a tentative filter.
    first = run_agent(service, symptom)

    assert first["toolsUsed"] == []
    assert "general medicine" in first["message"].lower()
    assert "preferred directory filter" in first["message"].lower()
    assert "separately" in first["message"].lower()
    assert len(calls) == 1
    assert agent_module._pending_appointment_requests[key] == symptom
    assert (
        agent_module._pending_appointment_suggested_departments[key]
        == "General Medicine"
    )

    # First yes: accept the filter only, not the directory search.
    second = run_agent(service, "Yes")

    assert second["toolsUsed"] == []
    assert "general medicine" in second["message"].lower()
    assert "read-only" in second["message"].lower()
    assert "reply yes or no" in second["message"].lower()
    assert len(calls) == 1
    assert key in agent_module._pending_appointment_requests
    assert key not in agent_module._pending_appointment_suggested_departments
    assert (
        agent_module._pending_appointment_departments[key]
        == "General Medicine"
    )

    # Second yes: permit read-only discovery, filtered to General Medicine.
    third = run_agent(service, "Yes")

    assert third["toolsUsed"] == ["findAppropriateDoctors"]
    assert third.get("doctorRecommendations")
    assert all(
        doctor["department"] == "General Medicine"
        for doctor in third["doctorRecommendations"]
    )
    assert len(calls) == 2
    assert key not in agent_module._pending_appointment_requests
    assert key not in agent_module._pending_appointment_departments

    # Discovery must not submit or book an appointment.
    assert "bookAppointment" not in third["toolsUsed"]
    assert "createAppointmentRequest" not in third["toolsUsed"]


@pytest.mark.parametrize(
    ("symptom", "expected_department"),
    [
        ("I have a headache.", "General Medicine"),
        (
            "I feel dizzy and my heart is beating fast.",
            "General Medicine",
        ),
    ],
)
def test_model_generated_consent_uses_general_medicine_fallback_for_unclear_symptoms(
    monkeypatch,
    symptom,
    expected_department,
):
    service = HospitalAgentService()
    calls = mock_llm(
        monkeypatch,
        response={
            "message": (
                "Would you like help checking available appointment options?"
            ),
            "toolsUsed": [],
        },
    )

    result = run_agent(service, symptom)

    key = "patient-001:consent-test"

    assert result["toolsUsed"] == []
    assert len(calls) == 1
    assert key in agent_module._pending_appointment_requests
    assert (
        agent_module._pending_appointment_suggested_departments[key]
        == expected_department
    )
    assert key not in agent_module._pending_appointment_departments


def test_model_generated_consent_does_not_offer_routine_search_for_urgent_symptoms(
    monkeypatch,
):
    service = HospitalAgentService()
    calls = mock_llm(
        monkeypatch,
        response={
            "message": (
                "Would you like help checking available appointment options?"
            ),
            "toolsUsed": [],
        },
    )

    result = run_agent(
        service,
        "I have chest pain and an irregular heartbeat.",
    )

    key = "patient-001:consent-test"

    assert result["toolsUsed"] == []
    assert "immediate medical care" in result["message"].casefold()
    assert "routine doctor directory" in result["message"].casefold()
    assert len(calls) == 1
    assert key not in agent_module._pending_appointment_requests
    assert key not in agent_module._pending_appointment_suggested_departments
    assert key not in agent_module._pending_appointment_departments


@pytest.mark.parametrize(
    "department",
    sorted({
        doctor["department"]
        for doctor in agent_module.DOCTORS
        if doctor.get("department")
    }),
)
def test_model_generated_consent_preserves_explicit_department_filter(
    monkeypatch,
    department,
):
    service = HospitalAgentService()
    calls = mock_llm(
        monkeypatch,
        response={
            "message": (
                f"Would you like me to search the demonstration doctor "
                f"directory for available {department} doctors?"
            ),
            "toolsUsed": [],
        },
    )

    message = (
        f"I would like to explore doctors in the {department} "
        "department. Can you help me?"
    )

    first = run_agent(service, message)
    key = "patient-001:consent-test"

    # The model-generated consent question must not search yet.
    assert first["toolsUsed"] == []
    assert len(calls) == 1
    assert key in agent_module._pending_appointment_requests
    assert agent_module._pending_appointment_departments[key] == department

    # The patient's yes grants read-only discovery for the saved department.
    second = run_agent(service, "Yes")

    assert len(calls) == 2
    assert second["toolsUsed"] == ["findAppropriateDoctors"]
    assert second.get("doctorRecommendations")

    assert all(
        doctor["department"] == department
        for doctor in second["doctorRecommendations"]
    )

    assert key not in agent_module._pending_appointment_requests
    assert key not in agent_module._pending_appointment_departments

    # The patient must now choose from the filtered doctor recommendations.
    selection = agent_module._pending_appointment_selections[key]
    assert selection["status"] == "awaiting_doctor_selection"
    assert all(
        doctor["department"] == department
        for doctor in selection["doctors"]
    )

def test_indirect_appointment_offer_after_medical_question_keeps_symptom_department_filter(
    monkeypatch,
):
    service = HospitalAgentService()
    actual_response = (
        "To help me provide more relevant information from your medical "
        "records, would you like to share how long your headache has lasted "
        "or if you have other symptoms? Also, if you would like to explore "
        "appointment options with a doctor to discuss this, please let me "
        "know and I can help you check available times."
    )
    calls = mock_llm(
        monkeypatch,
        response={
            "message": actual_response,
            "toolsUsed": [],
        },
    )

    symptom = "I have a headache."
    key = "patient-001:consent-test"

    first = run_agent(service, symptom)

    assert first["toolsUsed"] == []
    assert len(calls) == 1
    assert key in agent_module._pending_appointment_requests
    assert agent_module._pending_appointment_requests[key] == symptom
    assert (
        agent_module._pending_appointment_suggested_departments[key]
        == "General Medicine"
    )
    assert "general medicine" in first["message"].lower()
    assert "separately" in first["message"].lower()

    # First yes accepts the suggested department only.
    second = run_agent(service, "Yes")

    assert second["toolsUsed"] == []
    assert "general medicine" in second["message"].lower()
    assert "read-only" in second["message"].lower()
    assert agent_module._pending_appointment_departments[key] == (
        "General Medicine"
    )

    # Second yes grants directory-search consent.
    third = run_agent(service, "Yes")

    assert third["toolsUsed"] == ["findAppropriateDoctors"]
    assert third.get("doctorRecommendations")
    assert all(
        doctor["department"] == "General Medicine"
        for doctor in third["doctorRecommendations"]
    )
    assert len(calls) == 2
    assert key not in agent_module._pending_appointment_requests
    assert key not in agent_module._pending_appointment_departments
    assert key not in agent_module._pending_appointment_suggested_departments
    assert "bookAppointment" not in third["toolsUsed"]
    assert "createAppointmentRequest" not in third["toolsUsed"]

def test_routine_general_medical_checkup_uses_general_medicine_workflow(
    monkeypatch,
):
    service = HospitalAgentService()
    calls = mock_llm(
        monkeypatch,
        response={
            "message": "Would you like help exploring appointment options?",
            "toolsUsed": [],
        },
    )

    prompt = (
        "I would like a general medical check-up. "
        "Can you help me find the appropriate department and its doctors?"
    )
    key = "patient-001:consent-test"

    first = run_agent(service, prompt)

    assert first["toolsUsed"] == []
    assert "general medicine" in first["message"].lower()
    assert "routine general medical check-up" in first["message"].lower()
    assert "preferred directory filter" in first["message"].lower()
    assert "separately" in first["message"].lower()
    assert calls == []

    assert agent_module._pending_appointment_requests[key] == prompt
    assert (
        agent_module._pending_appointment_suggested_departments[key]
        == "General Medicine"
    )

    # First yes accepts the suggested filter only.
    second = run_agent(service, "Yes")

    assert second["toolsUsed"] == []
    assert "general medicine" in second["message"].lower()
    assert "read-only" in second["message"].lower()
    assert "reply yes or no" in second["message"].lower()
    assert calls == []

    assert (
        agent_module._pending_appointment_departments[key]
        == "General Medicine"
    )
    assert key in agent_module._pending_appointment_requests

    # Second yes permits read-only directory discovery.
    third = run_agent(service, "Yes")

    assert third["toolsUsed"] == ["findAppropriateDoctors"]
    doctors = third.get("doctorRecommendations")
    assert doctors
    assert len(doctors) == 2
    assert all(
        doctor["department"] == "General Medicine"
        for doctor in doctors
    )
    assert {
        doctor["name"] for doctor in doctors
    } == {
        "Dr. Hana Tesfaye",
        "Dr. Samuel Bekele",
    }

    assert key not in agent_module._pending_appointment_requests
    assert key not in agent_module._pending_appointment_departments
    assert key not in agent_module._pending_appointment_suggested_departments
    assert "bookAppointment" not in third["toolsUsed"]
    assert "createAppointmentRequest" not in third["toolsUsed"]

def test_short_routine_checkup_prompt_enters_general_medicine_workflow(
    monkeypatch,
):
    service = HospitalAgentService()
    calls = mock_llm(
        monkeypatch,
        response={
            "message": "Would you like help exploring appointment options?",
            "toolsUsed": [],
        },
    )

    prompt = "I'd like a routine check-up."
    key = "patient-001:consent-test"

    assert agent_module._is_appointment_workflow_request(prompt)

    result = run_agent(service, prompt)

    assert result["toolsUsed"] == []
    assert "general medicine" in result["message"].lower()
    assert "preferred directory filter" in result["message"].lower()
    assert "separately" in result["message"].lower()
    assert calls == []

    assert agent_module._pending_appointment_requests[key] == prompt
    assert (
        agent_module._pending_appointment_suggested_departments[key]
        == "General Medicine"
    )



def test_named_doctor_matching_supports_first_names_not_surnames():
    doctors = [
        {"id": "1", "name": "Dr. Kalkidan Mulu"},
        {"id": "2", "name": "Dr. Dawit Bekele"},
        {"id": "3", "name": "Dr. Dawit Hailu"},
        {"id": "4", "name": "Dr. Henok Assefa"},
        {"id": "5", "name": "Dr. Henok Alemu"},
    ]

    assert [
        doctor["name"]
        for doctor in agent_module._match_requested_doctors(
            "I need an appointment with Dr. Kalkidan Mulu",
            doctors,
        )
    ] == ["Dr. Kalkidan Mulu"]

    assert [
        doctor["name"]
        for doctor in agent_module._match_requested_doctors(
            "I need an appointment with Kalkidan",
            doctors,
        )
    ] == ["Dr. Kalkidan Mulu"]

    assert agent_module._match_requested_doctors(
        "I need an appointment with Bekele",
        doctors,
    ) == []

    assert [
        doctor["name"]
        for doctor in agent_module._match_requested_doctors(
            "I need an appointment with Dawit",
            doctors,
        )
    ] == ["Dr. Dawit Bekele", "Dr. Dawit Hailu"]

    assert [
        doctor["name"]
        for doctor in agent_module._match_requested_doctors(
            "I need an appointment with Henok",
            doctors,
        )
    ] == ["Dr. Henok Assefa", "Dr. Henok Alemu"]


def test_named_doctor_matching_is_case_and_punctuation_insensitive():
    doctors = [
        {"id": "1", "name": "Dr. Kalkidan Mulu"},
    ]

    matches = agent_module._match_requested_doctors(
        "appointment with DR KALKIDAN-MULU",
        doctors,
    )

    assert [doctor["id"] for doctor in matches] == ["1"]


def test_named_doctor_matching_returns_empty_for_unknown_name():
    doctors = [
        {"id": "1", "name": "Dr. Kalkidan Mulu"},
        {"id": "2", "name": "Dr. Dawit Bekele"},
    ]

    assert agent_module._match_requested_doctors(
        "I need an appointment with Dr. Unknown Person",
        doctors,
    ) == []


def test_named_doctor_search_returns_only_requested_doctor(
    monkeypatch,
):
    service = HospitalAgentService()
    doctors = [
        {
            "id": "doctor-kalkidan",
            "name": "Dr. Kalkidan Mulu",
            "department": "Ophthalmology",
            "specialties": [],
            "location": "Synthetic Demo Clinic B",
            "isAssignedDoctor": False,
            "dataSource": "synthetic_demo",
            "dataNotice": "Synthetic demo data only",
        },
        {
            "id": "doctor-dawit",
            "name": "Dr. Dawit Bekele",
            "department": "Respiratory Clinic",
            "specialties": [],
            "location": "Synthetic Demo Clinic A",
            "isAssignedDoctor": False,
            "dataSource": "synthetic_demo",
            "dataNotice": "Synthetic demo data only",
        },
    ]

    monkeypatch.setattr(
        agent_module,
        "_get_demo_doctors",
        lambda patient_id, department="": doctors,
    )

    calls = mock_llm(
        monkeypatch,
        response={
            "message": "Would you like to explore appointment options?",
            "toolsUsed": [],
        },
    )

    first = run_agent(
        service,
        "I need an appointment with Dr. Kalkidan Mulu.",
    )

    assert first["toolsUsed"] == []
    assert "yes or no" in first["message"].lower()

    result = run_agent(service, "Yes")

    assert result["toolsUsed"] == ["findAppropriateDoctors"]
    assert [
        doctor["name"]
        for doctor in result["doctorRecommendations"]
    ] == ["Dr. Kalkidan Mulu"]

    selection = agent_module._pending_appointment_selections[
        "patient-001:consent-test"
    ]
    assert selection["status"] == "awaiting_doctor_selection"
    assert [
        doctor["name"] for doctor in selection["doctors"]
    ] == ["Dr. Kalkidan Mulu"]

    assert "getAvailableAppointmentSlots" not in result["toolsUsed"]
    assert "bookAppointment" not in result["toolsUsed"]
    assert "createAppointmentRequest" not in result["toolsUsed"]
    assert len(calls) == 1


@pytest.mark.parametrize("requested_name", ["Mulu", "Bekele"])
def test_unmatched_standalone_doctor_name_is_not_matched_as_surname(
    monkeypatch,
    requested_name,
):
    service = HospitalAgentService()
    doctors = [
        {
            "id": "kalkidan-mulu",
            "name": "Dr. Kalkidan Mulu",
            "department": "Ophthalmology",
            "specialties": [],
            "location": "Demo Clinic A",
            "isAssignedDoctor": False,
            "dataSource": "synthetic_demo",
            "dataNotice": "Synthetic demo data only",
        },
        {
            "id": "dawit-bekele",
            "name": "Dr. Dawit Bekele",
            "department": "Respiratory Clinic",
            "specialties": [],
            "location": "Demo Clinic B",
            "isAssignedDoctor": False,
            "dataSource": "synthetic_demo",
            "dataNotice": "Synthetic demo data only",
        },
    ]

    monkeypatch.setattr(
        agent_module,
        "_get_demo_doctors",
        lambda patient_id, department="": doctors,
    )
    mock_llm(monkeypatch)

    request = f"I need an appointment with {requested_name}."
    first = run_agent(service, request)

    assert first["toolsUsed"] == []
    assert "yes or no" in first["message"].lower()

    result = run_agent(service, "Yes")
    key = "patient-001:consent-test"

    assert result["toolsUsed"] == ["findAppropriateDoctors"]
    assert result.get("doctorRecommendations") in (None, [])
    assert "couldn't find a doctor" in result["message"].lower()
    assert requested_name.lower() in result["message"].lower()
    assert "first name" not in result["message"].lower()
    assert "full name" not in result["message"].lower()
    assert "no appointment" in result["message"].lower()

    assert key not in agent_module._pending_appointment_selections
    assert "getAvailableAppointmentSlots" not in result["toolsUsed"]
    assert "bookAppointment" not in result["toolsUsed"]
    assert "createAppointmentRequest" not in result["toolsUsed"]


def test_ambiguous_named_doctor_search_preserves_all_matches(
    monkeypatch,
):
    service = HospitalAgentService()
    doctors = [
        {
            "id": "dawit-bekele",
            "name": "Dr. Dawit Bekele",
            "department": "Respiratory Clinic",
            "specialties": [],
            "location": "Demo Clinic A",
            "isAssignedDoctor": False,
            "dataSource": "synthetic_demo",
            "dataNotice": "Synthetic demo data only",
        },
        {
            "id": "dawit-hailu",
            "name": "Dr. Dawit Hailu",
            "department": "Endocrinology",
            "specialties": [],
            "location": "Demo Clinic B",
            "isAssignedDoctor": False,
            "dataSource": "synthetic_demo",
            "dataNotice": "Synthetic demo data only",
        },
        {
            "id": "kalkidan-mulu",
            "name": "Dr. Kalkidan Mulu",
            "department": "Ophthalmology",
            "specialties": [],
            "location": "Demo Clinic C",
            "isAssignedDoctor": False,
            "dataSource": "synthetic_demo",
            "dataNotice": "Synthetic demo data only",
        },
    ]

    monkeypatch.setattr(
        agent_module,
        "_get_demo_doctors",
        lambda patient_id, department="": doctors,
    )

    mock_llm(monkeypatch)

    first = run_agent(
        service,
        "I need an appointment with Dr. Dawit.",
    )
    assert "yes or no" in first["message"].lower()

    result = run_agent(service, "Yes")

    assert [
        doctor["name"]
        for doctor in result["doctorRecommendations"]
    ] == ["Dr. Dawit Bekele", "Dr. Dawit Hailu"]

    assert "multiple doctors" in result["message"].lower()
    assert "choose" in result["message"].lower()

    selection = agent_module._pending_appointment_selections[
        "patient-001:consent-test"
    ]
    assert selection["status"] == "awaiting_doctor_selection"
    assert len(selection["doctors"]) == 2
    assert "getAvailableAppointmentSlots" not in result["toolsUsed"]
    assert "bookAppointment" not in result["toolsUsed"]


def test_unknown_explicit_doctor_name_does_not_show_unrelated_doctors(
    monkeypatch,
):
    service = HospitalAgentService()
    doctors = [
        {
            "id": "kalkidan-mulu",
            "name": "Dr. Kalkidan Mulu",
            "department": "Ophthalmology",
            "specialties": [],
            "location": "Demo Clinic",
            "isAssignedDoctor": False,
            "dataSource": "synthetic_demo",
            "dataNotice": "Synthetic demo data only",
        },
    ]

    monkeypatch.setattr(
        agent_module,
        "_get_demo_doctors",
        lambda patient_id, department="": doctors,
    )

    mock_llm(monkeypatch)

    first = run_agent(
        service,
        "I need an appointment with Dr. Unknown Person.",
    )
    assert "yes or no" in first["message"].lower()

    result = run_agent(service, "Yes")

    assert "couldn't find a doctor named unknown" in result["message"].lower()
    assert "doctorRecommendations" not in result
    assert (
        "patient-001:consent-test"
        not in agent_module._pending_appointment_selections
    )
    assert "bookAppointment" not in result["toolsUsed"]
