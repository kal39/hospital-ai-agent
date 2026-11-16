"""Conservative symptom-to-department suggestions for directory navigation.

This module does not diagnose, triage, or determine clinical urgency.
Suggestions are tentative and must be confirmed by the patient.
"""

import re
from typing import TypedDict


class DepartmentSuggestion(TypedDict):
    department: str
    reason: str


# Keep these patterns deliberately narrow. Add mappings only after review.
_SYMPTOM_PATTERNS: list[tuple[str, re.Pattern[str], str]] = [
    (
        "Respiratory Clinic",
        re.compile(
            r"\b(?:persistent|ongoing|recurrent)\s+cough\b"
            r"|\bcough(?:ing)?\s+(?:for|lasting)\s+\d+\s+"
            r"(?:days?|weeks?)\b",
            re.IGNORECASE,
        ),
        "A persistent cough may be a reason to discuss the Respiratory Clinic "
        "as a possible starting point.",
    ),
    (
        "ENT",
        re.compile(
            r"\b(?:ear pain|earache|hearing loss|hearing difficulty|"
            r"ringing in (?:my )?ears)\b",
            re.IGNORECASE,
        ),
        "An ear or hearing concern may be a reason to discuss ENT "
        "as a possible starting point.",
    ),
    (
        "Dermatology",
        re.compile(
            r"\b(?:skin rash|itchy rash|rash on (?:my )?skin)\b",
            re.IGNORECASE,
        ),
        "A skin concern may be a reason to discuss Dermatology "
        "as a possible starting point.",
    ),
]

_NEGATION_PATTERN = re.compile(
    r"\b(?:no|not|never|without|don't have|do not have|"
    r"doesn't have|does not have)\b.{0,45}\b"
    r"(?:cough|ear pain|earache|hearing loss|hearing difficulty|"
    r"ringing in (?:my )?ears|skin rash|itchy rash|rash)\b",
    re.IGNORECASE,
)


def suggest_department(message: str) -> DepartmentSuggestion | None:
    """Return one tentative department suggestion, or None if uncertain."""
    if not isinstance(message, str) or not message.strip():
        return None

    # Avoid suggesting a department when a target symptom is explicitly
    # negated. This intentionally favors withholding a suggestion.
    if _NEGATION_PATTERN.search(message):
        return None

    matches = [
        (department, reason)
        for department, pattern, reason in _SYMPTOM_PATTERNS
        if pattern.search(message)
    ]

    # Multiple possible departments are ambiguous; do not choose one.
    if len(matches) != 1:
        return None

    department, reason = matches[0]
    return {
        "department": department,
        "reason": reason,
    }
