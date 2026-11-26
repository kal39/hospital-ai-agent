"""Authenticated API endpoints for synthetic in-portal notifications."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.auth import get_current_demo_staff, get_current_patient_id
from app.services.demo_scheduler import demo_scheduler
from app.services.notifications import (
    NOTIFICATION_EVENT_TYPES,
    NotificationNotFound,
    get_notification_service,
)


router = APIRouter(
    prefix="/api/patient/notifications",
    tags=["Patient Notifications"],
)

staff_router = APIRouter(
    prefix="/api/staff/notifications",
    tags=["Staff Notifications"],
)


def _notification_service():
    return get_notification_service(demo_scheduler)


@router.get("")
def list_patient_notifications(
    patient_id: Annotated[str, Depends(get_current_patient_id)],
    unread_only: bool = Query(default=False),
):
    """Return notifications belonging only to the authenticated patient."""

    notifications = _notification_service().list_patient_notifications(
        patient_id,
        unread_only=unread_only,
    )

    return {
        "notifications": notifications,
        "count": len(notifications),
        "dataSource": "synthetic_demo",
    }


@router.post("/{notification_id}/read")
def mark_patient_notification_read(
    notification_id: str,
    patient_id: Annotated[str, Depends(get_current_patient_id)],
):
    """Mark one of the authenticated patient's notifications as read."""

    try:
        notification = (
            _notification_service().mark_patient_notification_read(
                notification_id=notification_id,
                patient_id=patient_id,
            )
        )
    except NotificationNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found.",
        ) from None

    return {
        "notification": notification,
        "dataSource": "synthetic_demo",
    }


@staff_router.get("")
def list_staff_notifications(
    _staff: Annotated[str, Depends(get_current_demo_staff)],
    patient_id: str | None = Query(default=None, min_length=1, max_length=100),
    event_type: str | None = Query(default=None),
    unread_only: bool | None = Query(default=None),
):
    """Return notification history for authenticated demo staff."""

    if event_type is not None and event_type not in NOTIFICATION_EVENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Unsupported notification event type.",
        )

    try:
        notifications = _notification_service().list_staff_notifications(
            patient_id=patient_id,
            event_type=event_type,
            unread_only=unread_only,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    return {
        "notifications": notifications,
        "count": len(notifications),
        "dataSource": "synthetic_demo",
    }
