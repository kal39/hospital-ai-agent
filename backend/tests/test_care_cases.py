import pytest

from app.services.care_cases import (
    CareCaseConflict,
    DemoCareCaseService,
    get_care_case_service,
)
from app.services.demo_scheduler import DemoScheduler


@pytest.fixture
def care_case_service():
    scheduler = DemoScheduler()
    service = get_care_case_service(scheduler)

    yield service

    scheduler._connection.close()


def create_case(service, **overrides):
    values = {
        "patient_id": "patient-001",
        "conversation_id": "conversation-001",
        "reported_concern": "Severe chest pain and difficulty breathing.",
        "language": "en",
        "idempotency_key": "confirmation-001",
    }
    values.update(overrides)
    return service.create_case(**values)


def test_create_case_returns_synthetic_record(care_case_service):
    case = create_case(care_case_service)

    assert case["caseType"] == "emergency_concern"
    assert case["status"] == "registered"
    assert case["dataSource"] == "synthetic_demo"
    assert "SYNTHETIC DEMONSTRATION DATA" in case["dataNotice"]
    assert "not been sent to a real hospital" in case["dataNotice"]
    assert case["reportedConcern"] == (
        "Severe chest pain and difficulty breathing."
    )
    assert case["statusHistory"][0]["status"] == "registered"
    assert "patientId" not in case
    assert "idempotencyKey" not in case



def test_create_urgent_case_uses_urgent_notice(care_case_service):
    case = create_case(
        care_case_service,
        reported_concern="I have recurring dizziness.",
        idempotency_key="urgent-confirmation-001",
        case_type="urgent_concern",
    )

    assert case["caseType"] == "urgent_concern"
    assert case["dataSource"] == "synthetic_demo"
    assert "urgent follow-up concern" in case["dataNotice"].lower()
    assert "contact your healthcare team promptly" in (
        case["dataNotice"].lower()
    )
    assert "seek immediate medical attention" not in (
        case["dataNotice"].lower()
    )


def test_confirmation_key_cannot_be_reused_for_different_case_type(
    care_case_service,
):
    create_case(care_case_service)

    with pytest.raises(CareCaseConflict):
        create_case(
            care_case_service,
            case_type="urgent_concern",
        )

    count = care_case_service._connection.execute(
        "SELECT COUNT(*) FROM demo_care_cases"
    ).fetchone()[0]

    assert count == 1


def test_unsupported_case_type_is_rejected(care_case_service):
    with pytest.raises(ValueError, match="Unsupported care-case type"):
        create_case(care_case_service, case_type="routine_concern")


def test_patient_cannot_list_another_patients_cases(care_case_service):
    created = create_case(care_case_service)

    patient_one_cases = care_case_service.list_patient_cases("patient-001")
    patient_two_cases = care_case_service.list_patient_cases("patient-002")

    assert len(patient_one_cases) == 1
    assert patient_one_cases[0]["caseId"] == created["caseId"]
    assert patient_two_cases == []


def test_patient_cannot_retrieve_another_patients_case(care_case_service):
    created = create_case(care_case_service)

    result = care_case_service.get_patient_case(
        patient_id="patient-002",
        case_id=created["caseId"],
    )

    assert result is None


def test_same_confirmation_is_idempotent(care_case_service):
    first = create_case(care_case_service)
    second = create_case(care_case_service)

    assert first["caseId"] == second["caseId"]

    count = care_case_service._connection.execute(
        "SELECT COUNT(*) FROM demo_care_cases"
    ).fetchone()[0]

    assert count == 1


def test_reusing_confirmation_key_for_different_details_fails(
    care_case_service,
):
    create_case(care_case_service)

    with pytest.raises(CareCaseConflict):
        create_case(
            care_case_service,
            reported_concern="A different emergency concern.",
        )

    count = care_case_service._connection.execute(
        "SELECT COUNT(*) FROM demo_care_cases"
    ).fetchone()[0]

    assert count == 1


def test_unknown_patient_is_rejected(care_case_service):
    with pytest.raises(ValueError, match="Unknown synthetic patient"):
        create_case(care_case_service, patient_id="patient-999")


def test_invalid_language_is_rejected(care_case_service):
    with pytest.raises(ValueError, match="Unsupported language"):
        create_case(care_case_service, language="fr")


def test_empty_concern_is_rejected(care_case_service):
    with pytest.raises(ValueError, match="reported concern"):
        create_case(care_case_service, reported_concern="   ")


def test_service_factory_returns_same_instance(care_case_service):
    scheduler = care_case_service._scheduler

    assert get_care_case_service(scheduler) is care_case_service


def test_database_failure_does_not_return_a_registered_case(
    care_case_service,
):
    care_case_service._connection.execute(
        "DROP TABLE demo_care_cases"
    )
    care_case_service._connection.commit()

    with pytest.raises(Exception):
        create_case(care_case_service)



def test_patient_service_response_hides_priority_metadata(care_case_service):
    case = create_case(care_case_service)

    assert "prioritySuggestion" not in case
    assert "priorityReason" not in case
    assert "prioritySource" not in case
    assert "priorityCreatedAt" not in case
