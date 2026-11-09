"""Shared schemas for multimodal clinical decision support."""

from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class AnalysisModality(str, Enum):
    LABORATORY = "laboratory"
    RADIOLOGY_REPORT = "radiology_report"
    XRAY = "xray"
    CT_MRI = "ct_mri"
    GENERAL_DOCUMENT = "general_document"
    UNKNOWN = "unknown"


class AnalysisStatus(str, Enum):
    PRELIMINARY = "preliminary"
    INSUFFICIENT_DATA = "insufficient_data"
    ANALYSIS_UNAVAILABLE = "analysis_unavailable"
    UNSUPPORTED_INPUT = "unsupported_input"


class FindingConfidence(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    NOT_ASSESSED = "not_assessed"


class AbnormalityFlag(str, Enum):
    WITHIN_RANGE = "within_range"
    LOW = "low"
    HIGH = "high"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class ContractModel(BaseModel):
    """Base configuration shared by contract models."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )


class EvidenceReference(ContractModel):
    """Where a finding came from."""

    source: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=1, max_length=1000)
    excerpt: str | None = Field(default=None, max_length=2000)
    page_number: int | None = Field(
        default=None,
        alias="pageNumber",
        ge=1,
    )


class ClinicalFinding(ContractModel):
    """A finding with its source and supporting details."""

    name: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=2000)
    observed_value: str | None = Field(
        default=None,
        alias="observedValue",
        max_length=200,
    )
    unit: str | None = Field(default=None, max_length=80)
    reference_range: str | None = Field(
        default=None,
        alias="referenceRange",
        max_length=200,
    )
    observation_date: str | None = Field(
        default=None,
        alias="observationDate",
        max_length=100,
    )
    abnormality: AbnormalityFlag = AbnormalityFlag.UNKNOWN
    interpretation: str = Field(default="", max_length=3000)
    confidence: FindingConfidence = FindingConfidence.NOT_ASSESSED
    evidence: list[EvidenceReference] = Field(default_factory=list)


class PossibleExplanation(ContractModel):
    """A hypothesis for clinician review, not a confirmed diagnosis."""

    label: str = Field(min_length=1, max_length=200)
    rationale: str = Field(min_length=1, max_length=3000)
    supporting_findings: list[str] = Field(
        default_factory=list,
        alias="supportingFindings",
    )
    missing_information: list[str] = Field(
        default_factory=list,
        alias="missingInformation",
    )
    confidence: FindingConfidence = FindingConfidence.NOT_ASSESSED


class ClinicalAnalysisResponse(ContractModel):
    """Consistent response contract for all analysis modalities."""

    analysis_type: AnalysisModality = Field(alias="analysisType")
    status: AnalysisStatus
    summary: str = Field(default="", max_length=5000)
    findings: list[ClinicalFinding] = Field(default_factory=list)
    possible_explanations: list[PossibleExplanation] = Field(
        default_factory=list,
        alias="possibleExplanations",
    )
    uncertainty_notes: list[str] = Field(
        default_factory=list,
        alias="uncertaintyNotes",
    )
    limitations: list[str] = Field(default_factory=list)

    # The prototype must never represent its output as a confirmed diagnosis.
    requires_clinician_review: Literal[True] = Field(
        default=True,
        alias="requiresClinicianReview",
    )


class LaboratoryExplanation(ContractModel):
    """AI-generated explanation accompanying lab comparisons."""

    summary: str = Field(min_length=1, max_length=5000)
    possible_explanations: list[PossibleExplanation] = Field(
        default_factory=list,
        alias="possibleExplanations",
    )
    uncertainty_notes: list[str] = Field(
        default_factory=list,
        alias="uncertaintyNotes",
    )
    questions_for_clinician: list[str] = Field(
        default_factory=list,
        alias="questionsForClinician",
    )
    limitations: list[str] = Field(default_factory=list)
