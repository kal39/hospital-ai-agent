"""Shared public emergency-contact configuration."""

from typing import Any

from app.core.config import get_settings


def get_emergency_contacts() -> dict[str, Any]:
    """Return verified emergency contacts without exposing configuration secrets."""
    settings = get_settings()

    hospital_phone = settings.hospital_emergency_phone
    ambulance_phone = settings.ambulance_dispatch_phone
    alternative_phone = settings.alternative_emergency_phone

    available_numbers = [
        phone
        for phone in (hospital_phone, ambulance_phone, alternative_phone)
        if phone
    ]

    if hospital_phone and ambulance_phone:
        availability = "configured"
    elif available_numbers:
        availability = "partially_configured"
    else:
        availability = "not_configured"

    def clean(value: str | None) -> str | None:
        normalized = value.strip() if value else ""
        return normalized or None

    return {
        "active": True,
        "contactAvailability": availability,
        "hospitalName": clean(settings.hospital_name),
        "hospitalEmergencyPhone": clean(hospital_phone),
        "ambulanceDispatchPhone": clean(ambulance_phone),
        "alternativeEmergencyPhone": clean(alternative_phone),
        "hospitalAddress": clean(settings.hospital_address),
        "emergencyDirections": clean(settings.emergency_directions),
    }
