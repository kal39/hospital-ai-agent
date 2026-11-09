"""Deterministic laboratory comparisons; not a diagnostic engine."""

import math
import re
from collections import Counter
from typing import Any

from app.schemas.clinical_analysis import (
    AbnormalityFlag,
    AnalysisModality,
    AnalysisStatus,
    ClinicalAnalysisResponse,
    ClinicalFinding,
    EvidenceReference,
    FindingConfidence,
)

_RANGE = re.compile(
    r"^\s*(-?\d+(?:\.\d+)?)\s*[-–—]\s*(-?\d+(?:\.\d+)?)\s*$"
)


def _number(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    if not isinstance(value, (int, float, str)):
        return None
    try:
        result = float(value)
    except (ValueError, TypeError, OverflowError):
        return None
    return result if math.isfinite(result) else None


def _range(value: Any) -> tuple[float, float] | None:
    if not isinstance(value, str):
        return None
    match = _RANGE.fullmatch(value)
    if not match:
        return None
    low, high = float(match.group(1)), float(match.group(2))
    return (low, high) if low <= high else None


def _source_flag(value: Any) -> AbnormalityFlag | None:
    if not isinstance(value, str):
        return None
    status = value.strip().lower().replace("-", "_").replace(" ", "_")
    if status.startswith("critical"):
        return AbnormalityFlag.CRITICAL
    if status in {"high", "above", "above_range", "elevated"}:
        return AbnormalityFlag.HIGH
    if status in {"low", "below", "below_range"}:
        return AbnormalityFlag.LOW
    if status in {"normal", "within_range", "within_reference_range"}:
        return AbnormalityFlag.WITHIN_RANGE
    return None


def _classify(
    value: float | None,
    interval: tuple[float, float] | None,
    source_status: Any,
) -> AbnormalityFlag:
    source_flag = _source_flag(source_status)

    # Preserve a critical flag explicitly supplied by the source.
    if source_flag == AbnormalityFlag.CRITICAL:
        return source_flag

    if value is not None and interval is not None:
        low, high = interval
        if value < low:
            return AbnormalityFlag.LOW
        if value > high:
            return AbnormalityFlag.HIGH
        return AbnormalityFlag.WITHIN_RANGE

    # Preserve source flags if independent numeric comparison is impossible.
    if source_flag in {AbnormalityFlag.LOW, AbnormalityFlag.HIGH}:
        return source_flag
    return AbnormalityFlag.UNKNOWN


def analyze_lab_results(
    results: list[dict[str, Any]],
) -> ClinicalAnalysisResponse:
    """Compare numeric values with the reference ranges in supplied records."""
    if not results:
        return ClinicalAnalysisResponse(
            analysis_type=AnalysisModality.LABORATORY,
            status=AnalysisStatus.INSUFFICIENT_DATA,
            summary="No laboratory records were supplied.",
            uncertainty_notes=["No values were available for comparison."],
            limitations=["This engine does not diagnose medical conditions."],
        )

    findings: list[ClinicalFinding] = []
    uncertainties: list[str] = []
    sources: set[str] = set()

    for index, record in enumerate(results, start=1):
        if not isinstance(record, dict):
            uncertainties.append(f"Record {index} is not a valid object.")
            findings.append(
                ClinicalFinding(
                    name=f"Unusable record {index}",
                    abnormality=AbnormalityFlag.UNKNOWN,
                    interpretation="The record could not be interpreted.",
                )
            )
            continue

        name = str(record.get("testName") or "Unlabeled laboratory result")
        value = record.get("value")
        unit = record.get("unit")
        ref = record.get("referenceRange")
        date = record.get("date") or record.get("observationDate")
        source_status = record.get("status")
        source = str(record.get("dataSource") or "source_record")[:100]
        sources.add(source)

        numeric_value = _number(value)
        interval = _range(ref)
        flag = _classify(numeric_value, interval, source_status)

        if numeric_value is None:
            uncertainties.append(f"{name}: value is missing or non-numeric.")
        if interval is None:
            uncertainties.append(
                f"{name}: reference range is missing or unsupported; "
                "numeric comparison was not possible."
            )

        source_flag = _source_flag(source_status)
        if (
            numeric_value is not None
            and interval is not None
            and source_flag is not None
            and source_flag != AbnormalityFlag.CRITICAL
            and source_flag != flag
        ):
            uncertainties.append(
                f"{name}: recorded status '{source_status}' disagrees "
                f"with numeric comparison '{flag.value}'. Verify the report."
            )

        if flag == AbnormalityFlag.CRITICAL:
            interpretation = (
                "The source marks this result as critical. Confirm it "
                "against the original report and hospital escalation rules."
            )
        elif numeric_value is not None and interval is not None:
            if flag == AbnormalityFlag.LOW:
                interpretation = (
                    f"The value is below the supplied reference range ({ref}). "
                    "This comparison alone does not establish a diagnosis."
                )
            elif flag == AbnormalityFlag.HIGH:
                interpretation = (
                    f"The value is above the supplied reference range ({ref}). "
                    "This comparison alone does not establish a diagnosis."
                )
            else:
                interpretation = (
                    f"The value is within the supplied reference range ({ref}). "
                    "This alone does not establish that the patient is healthy."
                )
        elif source_flag in {AbnormalityFlag.LOW, AbnormalityFlag.HIGH}:
            interpretation = (
                f"The source labels this result as {flag.value}, but the "
                "numeric comparison could not be verified."
            )
        else:
            interpretation = (
                "The value or reference range could not be compared reliably."
            )

        excerpt = (
            f"testName={name}; value={value}; unit={unit}; "
            f"referenceRange={ref}; date={date}; status={source_status}"
        )
        findings.append(
            ClinicalFinding(
                name=name,
                description="Copied from the supplied laboratory record.",
                observed_value=None if value is None else str(value),
                unit=None if unit is None else str(unit),
                reference_range=None if ref is None else str(ref),
                observation_date=None if date is None else str(date),
                abnormality=flag,
                interpretation=interpretation,
                confidence=FindingConfidence.NOT_ASSESSED,
                evidence=[
                    EvidenceReference(
                        source=source,
                        description=f"Supplied laboratory record for {name}.",
                        excerpt=excerpt,
                    )
                ],
            )
        )

    counts = Counter(f.abnormality for f in findings)
    summary = (
        f"Reviewed {len(findings)} record(s): "
        f"{counts[AbnormalityFlag.LOW]} below and "
        f"{counts[AbnormalityFlag.HIGH]} above supplied reference ranges; "
        f"{counts[AbnormalityFlag.WITHIN_RANGE]} within range; "
        f"{counts[AbnormalityFlag.CRITICAL]} marked critical by the source; "
        f"{counts[AbnormalityFlag.UNKNOWN]} unclassified. "
        "This is a preliminary comparison, not a diagnosis."
    )

    limitations = [
        "Only simple numeric lower-to-upper reference ranges are compared.",
        "Units and reference ranges are preserved, not independently validated.",
        "No critical thresholds are invented by this engine.",
        "Abnormal results can have many causes; no diagnosis or medication change is recommended.",
    ]
    if any("synthetic" in s.lower() or "demo" in s.lower() for s in sources):
        limitations.append(
            "Source data is synthetic/demo data and is not a real patient's record."
        )

    return ClinicalAnalysisResponse(
        analysis_type=AnalysisModality.LABORATORY,
        status=AnalysisStatus.PRELIMINARY,
        summary=summary,
        findings=findings,
        uncertainty_notes=list(dict.fromkeys(uncertainties)),
        limitations=limitations,
        requires_clinician_review=True,
    )
