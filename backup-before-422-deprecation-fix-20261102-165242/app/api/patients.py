
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.auth import get_current_patient_id
from app.services.hospital import hospital_service
from app.services.llm import gemini_llm_service

router = APIRouter(prefix="/api/patient", tags=["Patient"])


@router.get("/profile")
async def get_current_patient_profile(
    patient_id: Annotated[str, Depends(get_current_patient_id)],
) -> dict[str, Any]:
    """Return the authenticated demo patient's labeled profile."""
    patient = hospital_service.get_patient_profile(patient_id)

    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient record not found.",
        )

    return {
        "patient": {
            "id": patient["id"],
            "name": f"{patient['firstName']} {patient['lastName']}",
            "dateOfBirth": patient["dateOfBirth"],
            "bloodType": patient["bloodType"],
            "allergies": patient["allergies"],
            "diagnoses": patient["diagnoses"],
            "dataSource": patient["dataSource"],
            "dataNotice": patient["dataNotice"],
        }
    }


@router.get("/labs")
async def get_current_patient_labs(
    patient_id: Annotated[str, Depends(get_current_patient_id)],
) -> dict[str, Any]:
    """Return laboratory results for the authenticated demo patient."""
    return {
        "results": hospital_service.get_all_lab_results(patient_id)
    }

@router.get("/labs/analysis")
async def analyze_current_patient_labs(
    patient_id: Annotated[str, Depends(get_current_patient_id)],
    include_explanation: bool = Query(
        default=False,
        alias="includeExplanation",
    ),
) -> dict[str, Any]:
    """Return deterministic lab comparison and optional AI explanation."""
    from app.services.lab_analysis import analyze_lab_results

    records = hospital_service.get_all_lab_results(patient_id)
    analysis = analyze_lab_results(records)
    payload = analysis.model_dump(by_alias=True, mode="json")

    # This prototype uses fictional local hospital records.
    # Make the data source explicit in every lab-analysis API response.
    payload["dataNotice"] = "SYNTHETIC DEMONSTRATION DATA: This information comes from fictional local development records, not a live hospital system. Do not treat it as a verified real patient record. Verify information against an authorized hospital system before making clinical or scheduling decisions."
    payload["dataSource"] = "synthetic_demo"

    if include_explanation:
        try:
            explanation = (
                await gemini_llm_service.generate_lab_explanation(analysis)
            )
        except RuntimeError as error:
            error_text = str(error).lower()

            if (
                "temporarily unavailable" in error_text
                or "not configured" in error_text
            ):
                raise HTTPException(
                    status_code=503,
                    detail=(
                        "The AI lab explanation is unavailable. Retry without "
                        "includeExplanation to receive the deterministic comparison."
                    ),
                ) from None

            print("[PATIENT LAB ANALYSIS] Structured explanation failed.")
            raise HTTPException(
                status_code=502,
                detail="The AI lab explanation could not be generated.",
            ) from None
        except Exception:
            print("[PATIENT LAB ANALYSIS] Unexpected explanation failure.")
            raise HTTPException(
                status_code=502,
                detail="The AI lab explanation could not be generated.",
            ) from None

        payload["aiExplanation"] = explanation.model_dump(
            by_alias=True,
            mode="json",
        )

    return payload
