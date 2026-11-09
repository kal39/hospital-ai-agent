"""Synthetic scheduling data for local development only.

All doctors, specialties, clinic locations, slots, and queue estimates
in this module are fictional. They are not live hospital data.
Replace this module with authorized hospital API calls before production.
"""

from datetime import date, datetime, timedelta
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
    {
        "id": "doctor-005",
        "name": "Dr. Abel Girma",
        "department": "Cardiology",
        "specialties": ["Cardiology", "Blood pressure assessment"],
        "location": "Synthetic Demo Clinic A",
    },
    {
        "id": "doctor-006",
        "name": "Dr. Selamawit Desta",
        "department": "Cardiology",
        "specialties": ["Cardiology", "Heart health follow-up"],
        "location": "Synthetic Demo Clinic B",
    },
    {
        "id": "doctor-007",
        "name": "Dr. Bethlehem Worku",
        "department": "Dermatology",
        "specialties": ["Dermatology", "Skin conditions"],
        "location": "Synthetic Demo Clinic A",
    },
    {
        "id": "doctor-008",
        "name": "Dr. Natnael Kebede",
        "department": "Dermatology",
        "specialties": ["Dermatology", "Hair and nail conditions"],
        "location": "Synthetic Demo Clinic B",
    },
    {
        "id": "doctor-009",
        "name": "Dr. Yared Solomon",
        "department": "Neurology",
        "specialties": ["Neurology", "Headache assessment"],
        "location": "Synthetic Demo Clinic A",
    },
    {
        "id": "doctor-010",
        "name": "Dr. Rahel Tadesse",
        "department": "Neurology",
        "specialties": ["Neurology", "Neurological follow-up"],
        "location": "Synthetic Demo Clinic B",
    },
    {
        "id": "doctor-011",
        "name": "Dr. Henok Assefa",
        "department": "Orthopedics",
        "specialties": ["Orthopedics", "Joint and bone conditions"],
        "location": "Synthetic Demo Clinic A",
    },
    {
        "id": "doctor-012",
        "name": "Dr. Mihret Abebe",
        "department": "Orthopedics",
        "specialties": ["Orthopedics", "Musculoskeletal follow-up"],
        "location": "Synthetic Demo Clinic B",
    },
    {
        "id": "doctor-013",
        "name": "Dr. Tigist Alemayehu",
        "department": "Pediatrics",
        "specialties": ["Pediatrics", "Child health"],
        "location": "Synthetic Demo Clinic A",
    },
    {
        "id": "doctor-014",
        "name": "Dr. Yonatan Fikru",
        "department": "Pediatrics",
        "specialties": ["Pediatrics", "Child wellness follow-up"],
        "location": "Synthetic Demo Clinic B",
    },
    {
        "id": "doctor-015",
        "name": "Dr. Meseret Kebede",
        "department": "Gynecology",
        "specialties": ["Gynecology", "Women's health"],
        "location": "Synthetic Demo Clinic A",
    },
    {
        "id": "doctor-016",
        "name": "Dr. Eden Berhanu",
        "department": "Gynecology",
        "specialties": ["Gynecology", "Routine women's health visits"],
        "location": "Synthetic Demo Clinic B",
    },
    {
        "id": "doctor-017",
        "name": "Dr. Fitsum Getachew",
        "department": "Ophthalmology",
        "specialties": ["Ophthalmology", "Eye examinations"],
        "location": "Synthetic Demo Clinic A",
    },
    {
        "id": "doctor-018",
        "name": "Dr. Kalkidan Mulu",
        "department": "Ophthalmology",
        "specialties": ["Ophthalmology", "Vision follow-up"],
        "location": "Synthetic Demo Clinic B",
    },
    {
        "id": "doctor-019",
        "name": "Dr. Bereket Alemu",
        "department": "Dental",
        "specialties": ["Dentistry", "Oral health"],
        "location": "Synthetic Demo Clinic A",
    },
    {
        "id": "doctor-020",
        "name": "Dr. Liya Mekonnen",
        "department": "Dental",
        "specialties": ["Dentistry", "Dental check-ups"],
        "location": "Synthetic Demo Clinic B",
    },
    {
        "id": "doctor-021",
        "name": "Dr. Ermias Tola",
        "department": "ENT",
        "specialties": ["Ear, Nose and Throat", "ENT assessment"],
        "location": "Synthetic Demo Clinic A",
    },
    {
        "id": "doctor-022",
        "name": "Dr. Hiwot Demissie",
        "department": "ENT",
        "specialties": ["Ear, Nose and Throat", "Hearing and sinus concerns"],
        "location": "Synthetic Demo Clinic B",
    },
    {
        "id": "doctor-023",
        "name": "Dr. Mulugeta Girma",
        "department": "Gastroenterology",
        "specialties": ["Gastroenterology", "Digestive health"],
        "location": "Synthetic Demo Clinic A",
    },
    {
        "id": "doctor-024",
        "name": "Dr. Saba Asrat",
        "department": "Gastroenterology",
        "specialties": ["Gastroenterology", "Digestive health follow-up"],
        "location": "Synthetic Demo Clinic B",
    },
    {
        "id": "doctor-025",
        "name": "Dr. Biniam Wolde",
        "department": "Urology",
        "specialties": ["Urology", "Urinary health"],
        "location": "Synthetic Demo Clinic A",
    },
    {
        "id": "doctor-026",
        "name": "Dr. Tsion Abate",
        "department": "Urology",
        "specialties": ["Urology", "Urological follow-up"],
        "location": "Synthetic Demo Clinic B",
    },
    {
        "id": "doctor-027",
        "name": "Dr. Nahom Girma",
        "department": "Psychiatry",
        "specialties": ["Psychiatry", "Mental wellness consultations"],
        "location": "Synthetic Demo Clinic A",
    },
    {
        "id": "doctor-028",
        "name": "Dr. Selam Getu",
        "department": "Psychiatry",
        "specialties": ["Psychiatry", "Follow-up consultations"],
        "location": "Synthetic Demo Clinic B",
    },
    {
        "id": "doctor-029",
        "name": "Dr. Dawit Hailu",
        "department": "Endocrinology",
        "specialties": ["Endocrinology", "Diabetes follow-up"],
        "location": "Synthetic Demo Clinic A",
    },
    {
        "id": "doctor-030",
        "name": "Dr. Almaz Tesfaye",
        "department": "Endocrinology",
        "specialties": ["Endocrinology", "Hormonal health"],
        "location": "Synthetic Demo Clinic B",
    },
    {
        "id": "doctor-031",
        "name": "Dr. Henok Alemu",
        "department": "Nephrology",
        "specialties": ["Nephrology", "Kidney health follow-up"],
        "location": "Synthetic Demo Clinic A",
    },
    {
        "id": "doctor-032",
        "name": "Dr. Mahlet Bekele",
        "department": "Nephrology",
        "specialties": ["Nephrology", "Kidney health"],
        "location": "Synthetic Demo Clinic B",
    },
]

# Existing fictional assignments are intentionally preserved.
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
    now: datetime | None = None,
) -> list[dict[str, Any]]:
    """Generate weekday demo slots; these are not actual appointments."""
    doctor = next(
        (item for item in DOCTORS if item["id"] == doctor_id),
        None,
    )
    if doctor is None:
        return []

    slots: list[dict[str, Any]] = []
    times = ("09:00", "10:30", "13:00", "14:30")
    now = now if now is not None else datetime.now().astimezone()

    for offset in range(days):
        slot_date = start_date + timedelta(days=offset)

        if slot_date.weekday() >= 5:
            continue

        for slot_time in times:
            if slot_date == now.date():
                current_time = now.time().replace(
                    tzinfo=None, second=0, microsecond=0
                )
                if datetime.strptime(slot_time, "%H:%M").time() <= current_time:
                    continue

            slots.append(
                {
                    "doctorId": doctor_id,
                    "date": slot_date.isoformat(),
                    "time": slot_time,
                    "department": doctor["department"],
                    "status": "demo_available",
                    "dataSource": DATA_SOURCE,
                }
            )

    return slots