
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.auth import get_current_patient_id
from app.services.hospital import hospital_service

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
