"""Tests for the clinical-analysis schema and modality router."""

import pytest
from pydantic import ValidationError

from app.schemas.clinical_analysis import (
    AnalysisModality,
    AnalysisStatus,
    ClinicalAnalysisResponse,
    ClinicalFinding,
    EvidenceReference,
)
from app.services.modality_router import (
    ModalityRouteDecision,
    RouteStatus,
    route_modality,
)


def test_response_uses_frontend_friendly_aliases():
    response = ClinicalAnalysisResponse(
        analysis_type=AnalysisModality.LABORATORY,
        status=AnalysisStatus.PRELIMINARY,
        summary="Preliminary example only.",
        findings=[
            ClinicalFinding(
                name="Example test",
                observed_value="10",
                unit="unit",
                reference_range="5-15",
                evidence=[
                    EvidenceReference(
                        source="uploaded_report",
                        description="Value copied from the example report.",
                        page_number=1,
                    )
                ],
            )
        ],
    )

    payload = response.model_dump(by_alias=True, mode="json")

    assert payload["analysisType"] == "laboratory"
    assert payload["requiresClinicianReview"] is True
    assert payload["findings"][0]["observedValue"] == "10"
    assert payload["findings"][0]["referenceRange"] == "5-15"
    assert payload["findings"][0]["evidence"][0]["pageNumber"] == 1


def test_response_cannot_disable_clinician_review():
    with pytest.raises(ValidationError):
        ClinicalAnalysisResponse(
            analysisType="laboratory",
            status="preliminary",
            requiresClinicianReview=False,
        )


def test_unselected_modality_requires_explicit_selection():
    decision = route_modality(None, "image/png")

    assert decision.modality == AnalysisModality.UNKNOWN
    assert decision.status == RouteStatus.REQUIRES_MODALITY_SELECTION
    assert decision.requires_modality_selection is True
    assert decision.sufficient_for_modality is False


def test_laboratory_pdf_routes_to_pending_lab_engine():
    decision = route_modality(
        AnalysisModality.LABORATORY,
        "application/pdf",
    )

    assert decision.status == RouteStatus.ENGINE_PENDING
    assert decision.current_format_supported is True
    assert decision.sufficient_for_modality is True
    assert decision.dedicated_engine_available is False


def test_typed_laboratory_values_can_be_routed_without_file():
    decision = route_modality(AnalysisModality.LABORATORY)

    assert decision.status == RouteStatus.ENGINE_PENDING
    assert decision.sufficient_for_modality is True


def test_xray_pdf_is_not_routed_as_an_image():
    decision = route_modality(
        AnalysisModality.XRAY,
        "application/pdf",
    )

    assert decision.status == RouteStatus.UNSUPPORTED_INPUT
    assert decision.current_format_supported is True
    assert decision.sufficient_for_modality is False


def test_xray_image_waits_for_a_dedicated_engine():
    decision = route_modality(AnalysisModality.XRAY, "image/png")

    assert decision.status == RouteStatus.ENGINE_PENDING
    assert decision.sufficient_for_modality is True
    assert decision.dedicated_engine_available is False


def test_ct_mri_requires_a_dicom_pipeline():
    decision = route_modality(AnalysisModality.CT_MRI, "image/png")

    assert decision.status == RouteStatus.REQUIRES_DICOM_PIPELINE
    assert decision.current_format_supported is False
    assert decision.sufficient_for_modality is False
    assert decision.requires_complete_study is True


def test_general_pdf_uses_existing_document_flow():
    decision = route_modality(
        AnalysisModality.GENERAL_DOCUMENT,
        "application/pdf",
    )

    assert decision.status == RouteStatus.EXISTING_DOCUMENT_FLOW
    assert decision.sufficient_for_modality is True
    assert decision.dedicated_engine_available is False


def test_route_decision_serializes_with_aliases():
    decision = route_modality(AnalysisModality.XRAY, "image/png")
    payload = decision.model_dump(by_alias=True, mode="json")

    assert payload["routeKey"] == "xray_imaging"
    assert payload["currentFormatSupported"] is True
    assert payload["dedicatedEngineAvailable"] is False
