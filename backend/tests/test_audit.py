"""Tests for privacy-conscious audit logging."""

from app.services import audit


def setup_function():
    audit.reset_audit_log()


def test_audit_records_timestamp_and_event():
    audit.record_audit_event({
        "patientId": "patient-001",
        "conversationId": "conversation-123",
        "event": "SAFETY_BLOCK",
        "details": {"urgent": True, "language": "en"},
    })

    entries = audit.get_audit_log()

    assert len(entries) == 1
    assert entries[0]["event"] == "SAFETY_BLOCK"
    assert entries[0]["patientId"] == "patient-001"
    assert entries[0]["conversationId"] == "conversation-123"
    assert entries[0]["timestamp"]
    assert entries[0]["details"] == {
        "urgent": True,
        "language": "en",
    }


def test_sensitive_and_unapproved_detail_fields_are_removed():
    audit.record_audit_event({
        "patientId": "patient-001",
        "event": "DEMO_APPOINTMENT_BOOKED",
        "details": {
            "bookingId": "booking-123",
            "doctorId": "doctor-7",
            "date": "2030-05-10",
            "time": "09:00",
            "reason": "Sensitive patient information",
            "message": "Private medical details",
            "toolsUsed": ["get_appointments", "get_profile"],
            "dataSource": "synthetic_demo",
        },
    })

    entry = audit.get_audit_log()[0]

    assert entry["details"] == {
        "toolsUsed": ["get_appointments", "get_profile"],
        "dataSource": "synthetic_demo",
    }
    assert "Sensitive patient information" not in str(entry)
    assert "Private medical details" not in str(entry)
    assert "2030-05-10" not in str(entry)
    assert "09:00" not in str(entry)


def test_audit_event_does_not_print_to_terminal(capsys):
    audit.record_audit_event({
        "patientId": "patient-001",
        "event": "CROSS_PATIENT_REQUEST_BLOCKED",
        "details": {},
    })

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""


def test_returned_entries_cannot_mutate_internal_audit_log():
    audit.record_audit_event({
        "patientId": "patient-001",
        "event": "AGENT_EXECUTION",
        "details": {"language": "en", "toolsUsed": ["get_profile"]},
    })

    returned = audit.get_audit_log()
    returned[0]["event"] = "TAMPERED"
    returned[0]["details"]["toolsUsed"].append("unauthorized_tool")

    stored = audit.get_audit_log()[0]

    assert stored["event"] == "AGENT_EXECUTION"
    assert stored["details"]["toolsUsed"] == ["get_profile"]


def test_unknown_event_and_malformed_details_are_handled_safely():
    audit.record_audit_event({
        "event": "",
        "details": {},
    })
    audit.record_audit_event({
        "event": "TEST_EVENT",
        "details": "not a dictionary",
    })

    entries = audit.get_audit_log()

    assert len(entries) == 1
    assert entries[0]["event"] == "TEST_EVENT"
    assert entries[0]["details"] == {}


def test_audit_log_is_bounded():
    for index in range(1005):
        audit.record_audit_event({
            "event": f"TEST_EVENT_{index}",
            "details": {},
        })

    entries = audit.get_audit_log()

    assert len(entries) == 1000
    assert entries[0]["event"] == "TEST_EVENT_5"
    assert entries[-1]["event"] == "TEST_EVENT_1004"
