"""Fictional emergency department directory for the demonstration."""

from typing import Any


def get_emergency_directory() -> dict[str, Any]:
    """Return clearly identified fictional emergency department information."""

    return {
        "dataType": "fictional_demo",
        "facilityName": "Demo General Hospital",
        "departmentName": "Emergency Department",
        "floor": "Ground Floor",
        "roomNumber": "Room 1",
        "address": "Fictional demonstration location, Addis Ababa, Ethiopia",
        "directions": (
            "Sample directions only. This is not a real hospital location "
            "and must not be used for navigation."
        ),
        "doctors": [
            {
                "id": "demo-emergency-doctor-001",
                "name": "Dr. Dawit Bekele",
                "specialty": "Emergency Medicine Specialist",
                "profileType": "fictional_demo",
                "availability": "not_provided",
            },
            {
                "id": "demo-emergency-doctor-002",
                "name": "Dr. Selamawit Alemu",
                "specialty": "Emergency Physician",
                "profileType": "fictional_demo",
                "availability": "not_provided",
            },
            {
                "id": "demo-emergency-doctor-003",
                "name": "Dr. Nahom Girma",
                "specialty": "Emergency and Critical Care",
                "profileType": "fictional_demo",
                "availability": "not_provided",
            },
        ],
    }
