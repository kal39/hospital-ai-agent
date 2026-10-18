"""Hospital medical glossary with unverified translations disabled.

Amharic medical translations must be reviewed against the hospital-approved
glossary before being used in patient-facing clinical explanations.
"""

from typing import TypedDict


class MedicalTerm(TypedDict):
    english: str
    amharic: str
    explanation: str


MEDICAL_GLOSSARY: list[MedicalTerm] = [
    {
        "english": "Hemoglobin",
        "amharic": "",
        "explanation": (
            "A protein in red blood cells that carries oxygen "
            "through the body."
        ),
    },
    {
        "english": "Fasting Blood Glucose",
        "amharic": "",
        "explanation": (
            "The amount of glucose in the blood after fasting."
        ),
    },
    {
        "english": "Creatinine",
        "amharic": "",
        "explanation": (
            "A substance commonly measured to help assess kidney function."
        ),
    },
    {
        "english": "Blood Pressure",
        "amharic": "",
        "explanation": (
            "The force of blood against the walls of blood vessels."
        ),
    },
    {
        "english": "Hypertension",
        "amharic": "",
        "explanation": "Persistently elevated blood pressure.",
    },
]


def get_glossary_context() -> str:
    """Format terms without inventing unapproved translations."""
    entries = []

    for term in MEDICAL_GLOSSARY:
        entry = f"{term['english']}: {term['explanation']}"
        if term["amharic"].strip():
            entry += f" Approved Amharic term: {term['amharic']}."
        entries.append(entry)

    entries.append(
        "Amharic medical translations are unavailable until reviewed "
        "and approved by the hospital. Do not invent medical translations."
    )
    return "\\n".join(entries)
