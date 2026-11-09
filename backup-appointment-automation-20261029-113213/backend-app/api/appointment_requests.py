"""Patient-facing API for demo appointment requests."""

from datetime import date
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.core.auth import get_current_patient_id
from app.services.appointment_requests import (
    AppointmentRequestConflict,
    AppointmentRequestNotFound,
    demo_appointment_request_service,
)

router = APIRouter(
    prefix="/api/patient/appointment-requests",
    tags=["Appointment Requests"],
)


class AppointmentRequestCreate(BaseModel):
    """Fields a patient may provide when requesting an appointment."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    department: str | None = Field(default=None, max_length=100)
    preferredDoctor: str | None = Field(default=None, max_length=120)
    preferredDateStart: date | None = None
    preferredDateEnd: date | None = None
    reason: str = Field(min_length=10, max_length=2000)

    @model_validator(mode="after")
    def validate_preferred_dates(self) -> "AppointmentRequestCreate":
        if (
            self.preferredDateStart is not None
            and self.preferredDateEnd is not None
            and self.preferredDateEnd < self.preferredDateStart
        ):
            raise ValueError(
                "preferredDateEnd must be on or after preferredDateStart."
            )

        return self


def _map_request_error(
    error: AppointmentRequestNotFound | AppointmentRequestConflict,
) -> HTTPException:
    if isinstance(error, AppointmentRequestNotFound):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment request not found.",
        )

    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=str(error),
    )


@router.post("", status_code=status.HTTP_201_CREATED)
async def submit_appointment_request(
    body: AppointmentRequestCreate,
    patient_id: Annotated[str, Depends(get_current_patient_id)],
) -> dict[str, Any]:
    """Create a request for the authenticated synthetic patient."""
    try:
        request = demo_appointment_request_service.create_request(
            patient_id=patient_id,
            department=body.department or None,
            preferred_doctor=body.preferredDoctor or None,
            preferred_date_start=body.preferredDateStart,
            preferred_date_end=body.preferredDateEnd,
            reason=body.reason,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from None

    return {"request": request}


@router.get("")
async def list_appointment_requests(
    patient_id: Annotated[str, Depends(get_current_patient_id)],
) -> dict[str, Any]:
    """List only requests owned by the authenticated synthetic patient."""
    return {
        "requests": demo_appointment_request_service.list_patient_requests(
            patient_id
        ),
        "dataSource": "synthetic_demo",
    }


@router.get("/{request_id}")
async def get_appointment_request(
    request_id: str,
    patient_id: Annotated[str, Depends(get_current_patient_id)],
) -> dict[str, Any]:
    """Get one request, enforcing patient ownership."""
    try:
        request = demo_appointment_request_service.get_patient_request(
            patient_id=patient_id,
            request_id=request_id,
        )
    except AppointmentRequestNotFound as error:
        raise _map_request_error(error) from None

    return {"request": request}


@router.post("/{request_id}/cancel")
async def cancel_appointment_request(
    request_id: str,
    patient_id: Annotated[str, Depends(get_current_patient_id)],
) -> dict[str, Any]:
    """Cancel an eligible request, not an already confirmed appointment."""
    try:
        request = demo_appointment_request_service.cancel_patient_request(
            patient_id=patient_id,
            request_id=request_id,
        )
    except (
        AppointmentRequestNotFound,
        AppointmentRequestConflict,
    ) as error:
        raise _map_request_error(error) from None

    return {"request": request}
