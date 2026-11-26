"""Public read-only hospital emergency information endpoints."""

from fastapi import APIRouter

from app.services.emergency_contacts import get_emergency_contacts
from app.services.emergency_directory import get_emergency_directory

router = APIRouter(prefix="/api", tags=["Emergency Contacts"])


@router.get("/emergency-contacts")
async def read_emergency_contacts() -> dict:
    """Return general hospital emergency contact information."""
    return get_emergency_contacts()


@router.get("/emergency-directory")
async def read_emergency_directory() -> dict | None:
    """Return the development directory, or null outside development."""
    return get_emergency_directory()
