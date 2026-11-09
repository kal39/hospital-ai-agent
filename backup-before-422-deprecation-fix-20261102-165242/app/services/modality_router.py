"""Deterministic routing decisions for clinical-analysis inputs.

This module routes inputs but does not perform clinical interpretation.
"""

from enum import Enum

from pydantic import Field

from app.schemas.clinical_analysis import (
    AnalysisModality,
    ContractModel,
)


CURRENT_UPLOAD_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "application/pdf",
}

IMAGE_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
}


class RouteStatus(str, Enum):
    REQUIRES_MODALITY_SELECTION = "requires_modality_selection"
    REQUIRES_ATTACHMENT = "requires_attachment"
    UNSUPPORTED_INPUT = "unsupported_input"
    REQUIRES_DICOM_PIPELINE = "requires_dicom_pipeline"
    ENGINE_PENDING = "engine_pending"
    EXISTING_DOCUMENT_FLOW = "existing_document_flow"


class ModalityRouteDecision(ContractModel):
    """Describes where an input should go and current limitations."""

    modality: AnalysisModality
    route_key: str = Field(alias="routeKey")
    status: RouteStatus
    current_format_supported: bool = Field(alias="currentFormatSupported")
    sufficient_for_modality: bool = Field(alias="sufficientForModality")
    dedicated_engine_available: bool = Field(
        default=False,
        alias="dedicatedEngineAvailable",
    )
    requires_complete_study: bool = Field(
        default=False,
        alias="requiresCompleteStudy",
    )
    requires_modality_selection: bool = Field(
        default=False,
        alias="requiresModalitySelection",
    )
    note: str = Field(min_length=1, max_length=1000)


def route_modality(
    modality: AnalysisModality | str | None,
    mime_type: str | None = None,
) -> ModalityRouteDecision:
    """Resolve an explicit modality without guessing from a filename."""
    if modality is None:
        selected = AnalysisModality.UNKNOWN
    else:
        try:
            selected = AnalysisModality(modality)
        except ValueError:
            selected = AnalysisModality.UNKNOWN

    format_supported = (
        mime_type is None
        or mime_type in CURRENT_UPLOAD_MIME_TYPES
    )

    if selected == AnalysisModality.UNKNOWN:
        return ModalityRouteDecision(
            modality=selected,
            routeKey="needs_modality_selection",
            status=RouteStatus.REQUIRES_MODALITY_SELECTION,
            currentFormatSupported=format_supported,
            sufficientForModality=False,
            requiresModalitySelection=True,
            note=(
                "Select the input type explicitly. Do not infer a modality "
                "from the filename or assume that an arbitrary image is "
                "a diagnostic study."
            ),
        )

    if selected == AnalysisModality.CT_MRI:
        # A single image or PDF is not a substitute for a complete study.
        return ModalityRouteDecision(
            modality=selected,
            routeKey="ct_mri_dicom_pipeline",
            status=RouteStatus.REQUIRES_DICOM_PIPELINE,
            currentFormatSupported=False,
            sufficientForModality=False,
            dedicatedEngineAvailable=False,
            requiresCompleteStudy=True,
            note=(
                "Full CT/MRI analysis requires a suitable study-ingestion "
                "pipeline, normally including DICOM study data. The current "
                "chat upload endpoint does not accept DICOM studies, and "
                "the dedicated imaging engine has not been implemented."
            ),
        )

    if selected == AnalysisModality.XRAY:
        if mime_type is None:
            return ModalityRouteDecision(
                modality=selected,
                routeKey="xray_imaging",
                status=RouteStatus.REQUIRES_ATTACHMENT,
                currentFormatSupported=False,
                sufficientForModality=False,
                note="An X-ray image is required for this modality.",
            )

        if mime_type not in IMAGE_MIME_TYPES:
            return ModalityRouteDecision(
                modality=selected,
                routeKey="xray_imaging",
                status=RouteStatus.UNSUPPORTED_INPUT,
                currentFormatSupported=format_supported,
                sufficientForModality=False,
                note=(
                    "The X-ray route expects an image file. A PDF may "
                    "instead be a written radiology report and should be "
                    "routed as a radiology report when appropriate."
                ),
            )

        return ModalityRouteDecision(
            modality=selected,
            routeKey="xray_imaging",
            status=RouteStatus.ENGINE_PENDING,
            currentFormatSupported=True,
            sufficientForModality=True,
            dedicatedEngineAvailable=False,
            note=(
                "The format can be uploaded, but a validated X-ray analysis "
                "engine is not yet integrated. Do not present the existing "
                "general LLM response as a validated diagnostic result."
            ),
        )

    if selected == AnalysisModality.GENERAL_DOCUMENT:
        if mime_type is None:
            return ModalityRouteDecision(
                modality=selected,
                routeKey="general_document",
                status=RouteStatus.REQUIRES_ATTACHMENT,
                currentFormatSupported=False,
                sufficientForModality=False,
                note="Attach a supported document for document explanation.",
            )

        if not format_supported:
            return ModalityRouteDecision(
                modality=selected,
                routeKey="general_document",
                status=RouteStatus.UNSUPPORTED_INPUT,
                currentFormatSupported=False,
                sufficientForModality=False,
                note="The current upload endpoint does not accept this file type.",
            )

        return ModalityRouteDecision(
            modality=selected,
            routeKey="general_document",
            status=RouteStatus.EXISTING_DOCUMENT_FLOW,
            currentFormatSupported=True,
            sufficientForModality=True,
            dedicatedEngineAvailable=False,
            note=(
                "The existing assistant can receive this file for general "
                "document explanation. This does not provide structured "
                "clinical analysis or a confirmed diagnosis."
            ),
        )

    # Laboratory values may be typed or uploaded in a supported file.
    # A written radiology report may similarly be supplied as text or file.
    if mime_type is not None and not format_supported:
        return ModalityRouteDecision(
            modality=selected,
            routeKey=selected.value,
            status=RouteStatus.UNSUPPORTED_INPUT,
            currentFormatSupported=False,
            sufficientForModality=False,
            note="The current upload endpoint does not accept this file type.",
        )

    return ModalityRouteDecision(
        modality=selected,
        routeKey=selected.value,
        status=RouteStatus.ENGINE_PENDING,
        currentFormatSupported=True,
        sufficientForModality=True,
        dedicatedEngineAvailable=False,
        note=(
            "The input type is recognized, but the dedicated structured "
            "clinical-analysis engine has not yet been implemented."
        ),
    )
