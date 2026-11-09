"""Patient-facing API for demo appointment requests."""

from datetime import date
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.core.auth import get_current_demo_staff, get_current_patient_id
from app.data.scheduling import DATA_SOURCE, DOCTORS
from app.services.audit import record_audit_event
from app.services.demo_scheduler import (
    DEMO_NOTICE,
    BookingConflictError,
    demo_scheduler,
)
from app.services.appointment_requests import (
    AppointmentRequestConflict,
    AppointmentRequestNotFound,
    get_appointment_request_service,
)


staff_router = APIRouter(
    prefix="/api/staff/appointment-requests",
    tags=["Staff Appointment Requests"],
)

router = APIRouter(
    prefix="/api/patient/appointment-requests",
    tags=["Appointment Requests"],
)


def _request_service():
    """Resolve the request service belonging to the active scheduler."""
    return get_appointment_request_service(demo_scheduler)


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


class StaffApproveRequest(BaseModel):
    """Doctor and slot selected by authorized demo staff."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    doctorId: str = Field(min_length=1, max_length=64)
    date: date
    time: str = Field(pattern=r"^(09:00|10:30|13:00|14:30)$")


class StaffDeclineRequest(BaseModel):
    """A decline decision must include a clear reason."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    reason: str = Field(min_length=10, max_length=500)


@staff_router.get("")
async def list_staff_appointment_requests(
    _staff_id: Annotated[str, Depends(get_current_demo_staff)],
) -> dict[str, Any]:
    """List synthetic appointment requests for authenticated demo staff."""
    requests = _request_service().list_staff_requests()

    return {
        "requests": requests,
        "dataSource": "synthetic_demo",
        "dataNotice": (
            "These are fictional local demo requests, not a live hospital queue. "
            "They persist in the local demo database across backend restarts."
        ),
    }


@staff_router.post("/{request_id}/approve")
async def approve_staff_appointment_request(
    request_id: str,
    body: StaffApproveRequest,
    staff_id: Annotated[str, Depends(get_current_demo_staff)],
) -> dict[str, Any]:
    """Approve an eligible request by creating a synthetic demo booking."""
    doctor = next(
        (item for item in DOCTORS if item["id"] == body.doctorId),
        None,
    )

    if doctor is None:
        raise HTTPException(status_code=422, detail="Doctor not found.")

    if body.date < date.today():
        raise HTTPException(
            status_code=422,
            detail="Appointment date cannot be in the past.",
        )

    try:
        result = _request_service().approve_request(
            request_id=request_id,
            doctor=doctor,
            appointment_date=body.date.isoformat(),
            appointment_time=body.time,
            booking_factory=demo_scheduler.book_appointment,
            decided_by=staff_id,
        )

    except AppointmentRequestNotFound:
        raise HTTPException(
            status_code=404,
            detail="Appointment request not found.",
        ) from None

    except AppointmentRequestConflict as error:
        raise HTTPException(status_code=409, detail=str(error)) from None

    except BookingConflictError as error:
        raise HTTPException(status_code=409, detail=str(error)) from None

    except ValueError as error:
        message = str(error)
        code = 409 if any(
            term in message.casefold()
            for term in ("full", "already have")
        ) else 422

        raise HTTPException(status_code=code, detail=message) from None

    booking = result.pop("booking")

    record_audit_event(
        {
            "patientId": booking.get("patientId"),
            "event": "demo_appointment_booked_from_request",
            "details": {
                "status": "appointment_confirmed",
                "dataSource": DATA_SOURCE,
            },
        }
    )

    return {
        "request": result,
        "booking": booking,
        "dataSource": DATA_SOURCE,
        "dataNotice": DEMO_NOTICE,
    }


@staff_router.post("/{request_id}/decline")
async def decline_staff_appointment_request(
    request_id: str,
    body: StaffDeclineRequest,
    staff_id: Annotated[str, Depends(get_current_demo_staff)],
) -> dict[str, Any]:
    """Decline an eligible request with a required reason."""
    try:
        request = _request_service().decline_request(
            request_id=request_id,
            reason=body.reason,
            decided_by=staff_id,
        )

    except AppointmentRequestNotFound:
        raise HTTPException(
            status_code=404,
            detail="Appointment request not found.",
        ) from None

    except AppointmentRequestConflict as error:
        raise HTTPException(status_code=409, detail=str(error)) from None

    return {
        "request": request,
        "dataSource": "synthetic_demo",
        "dataNotice": (
            "This is a fictional demo decision, not a real hospital decision."
        ),
    }


@router.post("", status_code=status.HTTP_201_CREATED)
async def submit_appointment_request(
    body: AppointmentRequestCreate,
    patient_id: Annotated[str, Depends(get_current_patient_id)],
) -> dict[str, Any]:
    """Create a request for the authenticated synthetic patient."""
    try:
        request = _request_service().create_request(
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
        "requests": _request_service().list_patient_requests(patient_id),
        "dataSource": "synthetic_demo",
    }


@router.get("/{request_id}")
async def get_appointment_request(
    request_id: str,
    patient_id: Annotated[str, Depends(get_current_patient_id)],
) -> dict[str, Any]:
    """Get one request, enforcing patient ownership."""
    try:
        request = _request_service().get_patient_request(
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
        request = _request_service().cancel_patient_request(
            patient_id=patient_id,
            request_id=request_id,
        )

    except (
        AppointmentRequestNotFound,
        AppointmentRequestConflict,
    ) as error:
        raise _map_request_error(error) from None

    return {"request": request}
