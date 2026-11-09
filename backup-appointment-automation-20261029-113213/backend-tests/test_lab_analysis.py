"""Tests for deterministic laboratory result analysis."""

from copy import deepcopy

import pytest

from app.schemas.clinical_analysis import (
    AbnormalityFlag,
    AnalysisStatus,
)
from app.services.hospital import HospitalService
from app.services.lab_analysis import analyze_lab_results


def make_record(value=10, reference_range="5-15", status="normal"):
    return {
        "id": "test-lab-1",
        "testName": "Example test",
        "value": value,
        "unit": "mg/dL",
        "referenceRange": reference_range,
        "status": status,
        "date": "2026-10-01",
        "dataSource": "synthetic_demo",
    }


@pytest.mark.parametrize(
    "value,expected",
    [
        (4.9, AbnormalityFlag.LOW),
        (5, AbnormalityFlag.WITHIN_RANGE),
        (10, AbnormalityFlag.WITHIN_RANGE),
        (15, AbnormalityFlag.WITHIN_RANGE),
        (15.1, AbnormalityFlag.HIGH),
    ],
)
def test_values_are_compared_with_supplied_range(value, expected):
    result = analyze_lab_results([make_record(value=value)])
    assert result.findings[0].abnormality == expected
    assert result.requires_clinician_review is True


def test_original_value_unit_range_and_date_are_preserved():
    result = analyze_lab_results([
        make_record(value=112, reference_range="70-99", status="high")
    ])
    finding = result.findings[0]

    assert finding.observed_value == "112"
    assert finding.unit == "mg/dL"
    assert finding.reference_range == "70-99"
    assert finding.observation_date == "2026-10-01"
    assert finding.evidence[0].source == "synthetic_demo"


def test_unsupported_reference_range_is_not_guessed():
    result = analyze_lab_results([
        make_record(value=10, reference_range="> 5")
    ])

    assert result.findings[0].abnormality == AbnormalityFlag.UNKNOWN
    assert result.uncertainty_notes


def test_missing_value_is_not_classified():
    result = analyze_lab_results([
        make_record(value=None, reference_range="5-15")
    ])

    assert result.findings[0].abnormality == AbnormalityFlag.UNKNOWN
    assert any("missing or non-numeric" in note for note in result.uncertainty_notes)


def test_non_numeric_value_is_not_classified():
    result = analyze_lab_results([
        make_record(value="not available")
    ])

    assert result.findings[0].abnormality == AbnormalityFlag.UNKNOWN


def test_source_critical_flag_is_preserved():
    result = analyze_lab_results([
        make_record(value=10, status="critical")
    ])

    assert result.findings[0].abnormality == AbnormalityFlag.CRITICAL
    assert "source marks" in result.findings[0].interpretation.lower()


def test_conflicting_source_status_is_reported():
    result = analyze_lab_results([
        make_record(value=10, status="high")
    ])

    assert result.findings[0].abnormality == AbnormalityFlag.WITHIN_RANGE
    assert any("disagrees" in note for note in result.uncertainty_notes)


def test_empty_results_report_insufficient_data():
    result = analyze_lab_results([])

    assert result.status == AnalysisStatus.INSUFFICIENT_DATA
    assert result.findings == []
    assert result.requires_clinician_review is True


def test_synthetic_data_limitation_is_present():
    result = analyze_lab_results([make_record()])

    assert any(
        "synthetic/demo" in item for item in result.limitations
    )


def test_source_records_are_not_mutated():
    records = [make_record(value=112, reference_range="70-99", status="high")]
    original = deepcopy(records)

    analyze_lab_results(records)

    assert records == original


def test_existing_synthetic_patient_results_are_compared():
    records = HospitalService().get_all_lab_results("patient-001")
    result = analyze_lab_results(records)

    flags = {finding.name: finding.abnormality for finding in result.findings}

    assert flags["Hemoglobin"] == AbnormalityFlag.WITHIN_RANGE
    assert flags["Fasting Blood Glucose"] == AbnormalityFlag.HIGH
    assert flags["Creatinine"] == AbnormalityFlag.WITHIN_RANGE
    assert result.status == AnalysisStatus.PRELIMINARY


def test_unknown_patient_has_no_results_to_analyze():
    records = HospitalService().get_all_lab_results("unknown-patient")
    result = analyze_lab_results(records)

    assert result.status == AnalysisStatus.INSUFFICIENT_DATA
