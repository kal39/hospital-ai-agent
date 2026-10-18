
"""Synthetic scheduling data for local development only.

These fictional doctors, slots, and queue estimates are not live hospital data.
Replace this module with authorized hospital API calls before production use.
"""

from datetime import date, timedelta
from typing import Any

DATA_SOURCE = "synthetic_demo"

DOCTORS: list[dict[str, Any]] = [
    {
        "id": "doctor-001",
        "name": "Dr. Hana Tesfaye",
        "department": "General Medicine",
        "specialties": ["General Medicine", "Hypertension follow-up"],
        "location": "Synthetic Demo Clinic A",
    },
    {
        "id": "doctor-002",
        "name": "Dr. Samuel Bekele",
        "department": "General Medicine",
        "specialties": ["General Medicine", "Chronic disease follow-up"],
        "location": "Synthetic Demo Clinic B",
    },
    {
        "id": "doctor-003",
        "name": "Dr. Dawit Bekele",
        "department": "Respiratory Clinic",
        "specialties": ["Respiratory Medicine", "Asthma follow-up"],
        "location": "Synthetic Demo Clinic A",
    },
    {
        "id": "doctor-004",
        "name": "Dr. Meron Alemu",
        "department": "Respiratory Clinic",
        "specialties": ["Respiratory Medicine"],
        "location": "Synthetic Demo Clinic B",
    },
]

# These assignments are fictional and exist only for demo patient IDs.
PATIENT_CARE_TEAMS: dict[str, dict[str, str]] = {
    "patient-001": {
        "doctorId": "doctor-001",
        "department": "General Medicine",
    },
    "patient-002": {
        "doctorId": "doctor-003",
        "department": "Respiratory Clinic",
    },
}


def generate_synthetic_slots(
    doctor_id: str,
    start_date: date,
    days: int = 14,
) -> list[dict[str, Any]]:
    """Generate weekday demo slots; these are not actual appointments."""
    slots: list[dict[str, Any]] = []
    times = ("09:00", "10:30", "13:00", "14:30")

    for offset in range(days):
        slot_date = start_date + timedelta(days=offset)

        if slot_date.weekday() >= 5:
            continue

        for time in times:
            slots.append(
                {
                    "doctorId": doctor_id,
                    "date": slot_date.isoformat(),
                    "time": time,
                    "department": next(
                        (
                            doctor["department"]
                            for doctor in DOCTORS
                            if doctor["id"] == doctor_id
                        ),
                        "Unknown",
                    ),
                    "status": "demo_available",
                    "dataSource": DATA_SOURCE,
                }
            )

    return slots
