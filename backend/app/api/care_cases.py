"""Patient and staff APIs for synthetic emergency care cases."""

from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from app.core.auth import get_current_demo_staff, get_current_patient_id
from app.services.care_cases import (
    CareCaseConflict,
    CareCaseNotFound,
    get_care_case_service,
)
from app.services.demo_scheduler import demo_scheduler


router = APIRouter(
    prefix="/api/patient/care-cases",
    tags=["Patient Care Cases"],
)

staff_router = APIRouter(
    prefix="/api/staff/care-cases",
    tags=["Staff Care Cases"],
)


def _care_case_service():
    """Resolve the care-case service using the active demo database."""
    return get_care_case_service(demo_scheduler)


class StaffCareCaseStatusUpdate(BaseModel):
    """A staff member may advance a case by one workflow step."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    status: Literal["acknowledged", "in_review", "resolved"]
    note: str | None = Field(default=None, max_length=300)


def _map_care_case_error(
    error: CareCaseNotFound | CareCaseConflict,
) -> HTTPException:
    if isinstance(error, CareCaseNotFound):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Care case not found.",
        )

    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=str(error),
    )


# Patient endpoints

@router.get("")
async def list_patient_care_cases(
    patient_id: Annotated[str, Depends(get_current_patient_id)],
) -> dict[str, Any]:
    """List only synthetic care cases owned by the authenticated patient."""
    return {
        "cases": _care_case_service().list_patient_cases(patient_id),
        "dataSource": "synthetic_demo",
    }


@router.get("/{case_id}")
async def get_patient_care_case(
    case_id: str,
    patient_id: Annotated[str, Depends(get_current_patient_id)],
) -> dict[str, Any]:
    """Retrieve one case only when it belongs to the authenticated patient."""
    case = _care_case_service().get_patient_case(
        patient_id=patient_id,
        case_id=case_id,
    )

    if case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Care case not found.",
        )

    return {"case": case, "dataSource": "synthetic_demo"}


# Staff endpoints

@staff_router.get("")
async def list_staff_care_cases(
    _staff_id: Annotated[str, Depends(get_current_demo_staff)],
) -> dict[str, Any]:
    """List synthetic care cases for authenticated demo staff."""
    return {
        "cases": _care_case_service().list_staff_cases(),
        "dataSource": "synthetic_demo",
    }


@staff_router.post("/{case_id}/status")
async def update_staff_care_case_status(
    case_id: str,
    payload: StaffCareCaseStatusUpdate,
    staff_id: Annotated[str, Depends(get_current_demo_staff)],
) -> dict[str, Any]:
    """Record one authorized staff workflow transition."""
    try:
        case = _care_case_service().update_case_status(
            case_id=case_id,
            new_status=payload.status,
            staff_id=staff_id,
            note=payload.note,
        )
    except (CareCaseNotFound, CareCaseConflict) as error:
        raise _map_care_case_error(error) from error
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error

    return {
        "case": case,
        "dataSource": "synthetic_demo",
    }
