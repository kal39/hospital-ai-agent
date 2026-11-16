from datetime import date, timedelta

import pytest

import app.services.appointment_requests as request_module
from app.services.appointment_requests import DemoAppointmentRequestService
from app.services.demo_scheduler import DemoScheduler


def create_test_request(
    service,
    *,
    patient_id="patient-001",
    key="test-idempotency-key-001",
    reason="I need a consultation for recurring headaches.",
    department="General Medicine",
):
    preferred_date = date.today() + timedelta(days=10)

    return service.create_request(
        patient_id=patient_id,
        department=department,
        preferred_doctor="Dr. Demo One",
        preferred_date_start=preferred_date,
        preferred_date_end=preferred_date,
        reason=reason,
        idempotency_key=key,
    )


def test_same_key_and_same_payload_returns_existing_request():
    scheduler = DemoScheduler()
    service = DemoAppointmentRequestService(scheduler)

    first = create_test_request(service)
    second = create_test_request(service)

    assert first["requestId"] == second["requestId"]
    assert first["status"] == second["status"]

    requests = service.list_patient_requests("patient-001")
    assert len(requests) == 1

    assert "idempotencyKey" not in first
    assert "patientId" not in first


def test_same_key_with_different_payload_is_rejected():
    scheduler = DemoScheduler()
    service = DemoAppointmentRequestService(scheduler)

    first = create_test_request(service)

    with pytest.raises(ValueError, match="different appointment details"):
        create_test_request(
            service,
            reason="I need an appointment for a different medical concern.",
        )

    requests = service.list_patient_requests("patient-001")
    assert len(requests) == 1
    assert requests[0]["requestId"] == first["requestId"]


def test_same_key_is_independent_between_patients():
    scheduler = DemoScheduler()
    service = DemoAppointmentRequestService(scheduler)

    first = create_test_request(service, patient_id="patient-001")
    second = create_test_request(service, patient_id="patient-002")

    assert first["requestId"] != second["requestId"]
    assert len(service.list_patient_requests("patient-001")) == 1
    assert len(service.list_patient_requests("patient-002")) == 1


def test_idempotency_survives_database_reopening(tmp_path):
    database_path = str(tmp_path / "appointment_requests.sqlite3")

    first_scheduler = DemoScheduler(db_path=database_path)
    first_service = DemoAppointmentRequestService(first_scheduler)

    first = create_test_request(first_service)

    first_scheduler._connection.close()

    second_scheduler = DemoScheduler(db_path=database_path)
    second_service = DemoAppointmentRequestService(second_scheduler)

    second = create_test_request(second_service)

    assert first["requestId"] == second["requestId"]
    assert len(second_service.list_patient_requests("patient-001")) == 1


def test_audit_failure_does_not_fail_committed_request(monkeypatch):
    scheduler = DemoScheduler()
    service = DemoAppointmentRequestService(scheduler)

    def failing_audit(event):
        raise RuntimeError("Simulated audit storage failure")

    monkeypatch.setattr(
        request_module,
        "record_audit_event",
        failing_audit,
    )

    created = create_test_request(service)

    assert created["requestId"]
    assert created["status"] == "submitted"

    retrieved = service.get_patient_request(
        patient_id="patient-001",
        request_id=created["requestId"],
    )

    assert retrieved["requestId"] == created["requestId"]
    assert retrieved["status"] == "submitted"

