
from typing import Any

PATIENTS: dict[str, dict[str, Any]] = {
    "patient-001": {
        "id": "patient-001",
        "firstName": "Abebe",
        "lastName": "Kebede",
        "dateOfBirth": "1998-04-15",
        "bloodType": "O+",
        "allergies": ["Penicillin"],
        "diagnoses": ["Hypertension"],
    },
    "patient-002": {
        "id": "patient-002",
        "firstName": "Sara",
        "lastName": "Bekele",
        "dateOfBirth": "2001-07-22",
        "bloodType": "A+",
        "allergies": ["None reported"],
        "diagnoses": ["Asthma"],
    },
}

LAB_RESULTS: dict[str, list[dict[str, Any]]] = {
    "patient-001": [
        {
            "id": "lab-001",
            "testName": "Hemoglobin",
            "value": 13.8,
            "unit": "g/dL",
            "referenceRange": "13.0-17.0",
            "status": "normal",
            "date": "2026-10-01",
        },
        {
            "id": "lab-002",
            "testName": "Fasting Blood Glucose",
            "value": 112,
            "unit": "mg/dL",
            "referenceRange": "70-99",
            "status": "high",
            "date": "2026-10-01",
        },
        {
            "id": "lab-003",
            "testName": "Creatinine",
            "value": 0.9,
            "unit": "mg/dL",
            "referenceRange": "0.7-1.3",
            "status": "normal",
            "date": "2026-10-01",
        },
    ],
    "patient-002": [
        {
            "id": "lab-004",
            "testName": "Hemoglobin",
            "value": 12.5,
            "unit": "g/dL",
            "referenceRange": "12.0-16.0",
            "status": "normal",
            "date": "2026-09-25",
        },
        {
            "id": "lab-005",
            "testName": "Fasting Blood Glucose",
            "value": 88,
            "unit": "mg/dL",
            "referenceRange": "70-99",
            "status": "normal",
            "date": "2026-09-25",
        },
    ],
}

MEDICATIONS: dict[str, list[dict[str, Any]]] = {
    "patient-001": [
        {
            "id": "med-001",
            "name": "Amlodipine",
            "dosage": "5 mg",
            "frequency": "Once daily",
            "instructions": "Take in the morning with or without food.",
            "active": True,
        },
    ],
    "patient-002": [
        {
            "id": "med-002",
            "name": "Example Inhaler",
            "dosage": "As prescribed",
            "frequency": "As prescribed",
            "instructions": (
                "Synthetic test record only. Follow the instructions "
                "provided by the treating clinician."
            ),
            "active": True,
        },
    ],
}

MEDICAL_HISTORY: dict[str, list[dict[str, Any]]] = {
    "patient-001": [
        {
            "id": "history-001",
            "date": "2026-08-15",
            "type": "visit",
            "title": "Routine follow-up",
            "description": "Routine hypertension follow-up.",
        },
        {
            "id": "history-002",
            "date": "2026-09-10",
            "type": "treatment",
            "title": "Medication review",
            "description": "Amlodipine therapy reviewed.",
        },
        {
            "id": "history-003",
            "date": "2026-10-01",
            "type": "visit",
            "title": "Laboratory testing",
            "description": "Routine blood laboratory tests performed.",
        },
    ],
    "patient-002": [
        {
            "id": "history-004",
            "date": "2026-08-20",
            "type": "visit",
            "title": "Example respiratory follow-up",
            "description": "Synthetic development record.",
        },
        {
            "id": "history-005",
            "date": "2026-09-25",
            "type": "visit",
            "title": "Laboratory testing",
            "description": "Synthetic laboratory test records added.",
        },
    ],
}

# Synthetic development data only. Replace with the hospital's
# authorized appointment API before using real patient records.
APPOINTMENTS: dict[str, list[dict[str, Any]]] = {
    "patient-001": [
        {
            "id": "appt-001",
            "date": "2026-11-20",
            "time": "09:30",
            "department": "General Medicine",
            "purpose": "Hypertension follow-up",
            "status": "scheduled",
            "location": "Synthetic Demo Clinic",
        },
    ],
    "patient-002": [
        {
            "id": "appt-002",
            "date": "2026-11-27",
            "time": "10:00",
            "department": "Respiratory Clinic",
            "purpose": "Respiratory follow-up",
            "status": "scheduled",
            "location": "Synthetic Demo Clinic",
        },
    ],
}


def get_patient_record(patient_id: str) -> dict[str, Any] | None:
    """Return a patient profile by its trusted internal ID."""
    return PATIENTS.get(patient_id)
