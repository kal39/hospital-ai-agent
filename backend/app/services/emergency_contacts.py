"""Shared public emergency-contact configuration."""

from typing import Any

from app.core.config import get_settings


def get_emergency_contacts() -> dict[str, Any]:
    """Return public contact details without exposing unverified phone numbers."""
    settings = get_settings()

    def clean(value: str | None) -> str | None:
        normalized = value.strip() if value else ""
        return normalized or None

    # Phone numbers remain unavailable until a verification mechanism
    # is implemented and the contacts have been independently confirmed.
    return {
        "active": True,
        "contactAvailability": "not_configured",
        "hospitalName": clean(settings.hospital_name),
        "hospitalEmergencyPhone": None,
        "ambulanceDispatchPhone": None,
        "alternativeEmergencyPhone": None,
        "hospitalAddress": clean(settings.hospital_address),
        "emergencyDirections": clean(settings.emergency_directions),
    }
