
from app.services.hospital import HospitalService


def test_get_patient_profile_returns_existing_patient():
    service = HospitalService()

    profile = service.get_patient_profile("patient-001")

    assert profile is not None
    assert profile["id"] == "patient-001"
    assert profile["firstName"] == "Abebe"
    assert profile["bloodType"] == "O+"


def test_get_patient_profile_returns_none_for_unknown_patient():
    service = HospitalService()

    assert service.get_patient_profile("unknown-patient") is None


def test_get_latest_lab_results_returns_latest_date_only():
    service = HospitalService()

    results = service.get_latest_lab_results("patient-001")

    assert len(results) == 3
    assert {result["date"] for result in results} == {"2026-10-01"}


def test_get_all_lab_results_returns_all_records():
    service = HospitalService()

    assert len(service.get_all_lab_results("patient-001")) == 3
    assert len(service.get_all_lab_results("patient-002")) == 2
    assert service.get_all_lab_results("unknown-patient") == []


def test_get_medications_returns_patient_specific_records():
    service = HospitalService()

    medications = service.get_medications("patient-001")

    assert len(medications) == 1
    assert medications[0]["name"] == "Amlodipine"
    assert service.get_medications("unknown-patient") == []


def test_get_medical_history_returns_patient_specific_records():
    service = HospitalService()

    history = service.get_medical_history("patient-001")

    assert len(history) == 3
    assert history[0]["id"] == "history-001"
    assert service.get_medical_history("unknown-patient") == []


def test_compare_lab_results_handles_missing_previous_results():
    service = HospitalService()

    comparisons = service.compare_lab_results("patient-001")

    assert len(comparisons) == 3
    assert all(item["previous"] is None for item in comparisons)
    assert all(item["change"] is None for item in comparisons)


def test_compare_lab_results_handles_unknown_patient():
    service = HospitalService()

    assert service.compare_lab_results("unknown-patient") == []
