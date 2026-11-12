import asyncio

import pytest

import app.services.agent as agent_module
from app.services.agent import HospitalAgentService


@pytest.fixture(autouse=True)
def isolate_agent_state(monkeypatch):
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


def run_agent(service, message, language="en"):
    return asyncio.run(
        service.run(
            user_message=message,
            patient_id="patient-001",
            conversation_id="upcoming-appointment-test",
            language=language,
            detail="normal",
        )
    )


def mock_llm(monkeypatch, tools_used=None):
    async def fake_generate_with_tools(**kwargs):
        return {
            "message": "Here are your appointments: ***",
            "toolsUsed": tools_used if tools_used is not None else ["getUpcomingAppointments"],
        }

    monkeypatch.setattr(
        agent_module.gemini_llm_service,
        "generate_with_tools",
        fake_generate_with_tools,
    )


def sample_appointments():
    return [
        {
            "bookingId": "appt-test-001",
            "date": "2026-11-20",
            "time": "09:30",
            "doctorName": "Dr. Hana Tesfaye",
            "department": "General Medicine",
            "purpose": "Hypertension follow-up",
            "status": "scheduled",
            "location": "Synthetic Demo Clinic A",
        },
        {
            "bookingId": "appt-test-002",
            "date": "2026-11-30",
            "time": "10:30",
            "doctorName": "Dr. Bereket Alemu",
            "department": "Dental",
            "purpose": "Dental consultation",
            "status": "confirmed_demo",
            "location": "Synthetic Demo Clinic A",
        },
    ]


def test_upcoming_appointments_are_formatted_from_patient_records(monkeypatch):
    mock_llm(monkeypatch)

    monkeypatch.setattr(
        agent_module.hospital_service,
        "get_upcoming_appointments",
        lambda patient_id: sample_appointments(),
    )

    result = run_agent(
        HospitalAgentService(),
        "What are my upcoming appointments?",
    )

    assert "November 20, 2026" in result["message"]
    assert "November 30, 2026" in result["message"]
    assert "Dr. Hana Tesfaye" in result["message"]
    assert "Dr. Bereket Alemu" in result["message"]
    assert "General Medicine" in result["message"]
    assert "Dental" in result["message"]
    assert "Hypertension follow-up" in result["message"]
    assert "Dental consultation" in result["message"]
    assert "Scheduled" in result["message"]
    assert "Confirmed (demo)" in result["message"]
    assert "Synthetic-data notice:" in result["message"]
    assert result["toolsUsed"] == ["getUpcomingAppointments"]


def test_upcoming_appointments_are_formatted_in_amharic(monkeypatch):
    mock_llm(monkeypatch)

    monkeypatch.setattr(
        agent_module.hospital_service,
        "get_upcoming_appointments",
        lambda patient_id: sample_appointments(),
    )

    result = run_agent(
        HospitalAgentService(),
        "የሚቀጥሉት ቀጠሮዎቼ ምንድናቸው?",
        language="am",
    )

    assert "የሚቀጥሉት ቀጠሮዎችዎ" in result["message"]
    assert "ቀን" in result["message"]
    assert "ሐኪም" in result["message"]
    assert "Dr. Hana Tesfaye" in result["message"]
    assert "Dr. Bereket Alemu" in result["message"]
    assert "November 20, 2026" in result["message"]


def test_empty_upcoming_appointments_are_reported_clearly(monkeypatch):
    mock_llm(monkeypatch)

    monkeypatch.setattr(
        agent_module.hospital_service,
        "get_upcoming_appointments",
        lambda patient_id: [],
    )

    result = run_agent(
        HospitalAgentService(),
        "What are my upcoming appointments?",
    )

    assert "couldn't find any upcoming appointments" in (
        result["message"].lower()
    )
    assert "Synthetic-data notice:" in result["message"]


def test_appointment_formatter_is_not_used_without_tool_call(monkeypatch):
    mock_llm(monkeypatch, tools_used=[])

    def unexpected_retrieval(patient_id):
        raise AssertionError("Appointment retrieval should not run.")

    monkeypatch.setattr(
        agent_module.hospital_service,
        "get_upcoming_appointments",
        unexpected_retrieval,
    )

    result = run_agent(
        HospitalAgentService(),
        "Please explain my medical records.",
    )

    assert "Here are your appointments: ***" in result["message"]
    assert result["toolsUsed"] == []
