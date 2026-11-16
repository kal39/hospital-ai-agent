"""Conservative symptom-to-department suggestions for directory navigation.

This module does not diagnose, triage, or determine clinical urgency.
Suggestions are tentative and must be confirmed by the patient.
Emergency screening must run before this matcher in the agent workflow.
"""

import re
from typing import TypedDict


class DepartmentSuggestion(TypedDict):
    department: str
    reason: str


# These are deliberately specific navigation phrases, not diagnostic rules.
# Broad or overlapping symptoms are intentionally left unmatched.
_SYMPTOM_PATTERNS: list[tuple[str, re.Pattern[str], str]] = [
    (
        "General Medicine",
        re.compile(
            r"\b(?:routine general check[- ]?up|general health check[- ]?up|"
            r"general medical consultation|general health consultation)\b",
            re.IGNORECASE,
        ),
        "A general health visit may be a reasonable starting point "
        "for discussing your concern.",
    ),
    (
        "Respiratory Clinic",
        re.compile(
            r"\b(?:persistent|ongoing|recurrent|chronic)\s+cough\b"
            r"|\bcough(?:ing)?\s+(?:for|lasting)\s+\d+\s+"
            r"(?:days?|weeks?)\b"
            r"|\b(?:wheezing|recurrent wheeze|asthma follow[- ]?up)\b",
            re.IGNORECASE,
        ),
        "A persistent cough, wheezing, or asthma follow-up may be a reason "
        "to discuss the Respiratory Clinic as a possible starting point.",
    ),
    (
        "Cardiology",
        re.compile(
            r"\b(?:heart palpitations|palpitations|irregular heartbeat|"
            r"racing heartbeat|heart beating irregularly|"
            r"cardiology follow[- ]?up)\b",
            re.IGNORECASE,
        ),
        "A heart-rhythm concern may be a reason to discuss Cardiology "
        "as a possible starting point.",
    ),
    (
        "Dermatology",
        re.compile(
            r"\b(?:skin rash|itchy rash|rash on (?:my )?skin|"
            r"eczema|acne|persistent itching|hair loss|nail changes)\b",
            re.IGNORECASE,
        ),
        "A skin, hair, or nail concern may be a reason to discuss "
        "Dermatology as a possible starting point.",
    ),
    (
        "Neurology",
        re.compile(
            r"\b(?:recurrent migraine|migraine attacks|"
            r"recurrent numbness|tingling in (?:my )?(?:hands?|feet|arms?|legs?)|"
            r"hand tremor|uncontrolled shaking|neurology follow[- ]?up)\b",
            re.IGNORECASE,
        ),
        "A recurring neurological concern may be a reason to discuss "
        "Neurology as a possible starting point.",
    ),
    (
        "Orthopedics",
        re.compile(
            r"\b(?:knee joint pain|hip joint pain|shoulder joint pain|"
            r"joint pain|pain in (?:my )?(?:knee|hip|shoulder)|"
            r"joint swelling|recurrent joint pain|orthopedic follow[- ]?up)\b",
            re.IGNORECASE,
        ),
        "A joint or musculoskeletal concern may be a reason to discuss "
        "Orthopedics as a possible starting point.",
    ),
    (
        "Pediatrics",
        re.compile(
            r"\b(?:my child needs (?:a )?(?:check[- ]?up|wellness visit)|"
            r"my baby needs (?:a )?(?:check[- ]?up|wellness visit)|"
            r"child wellness visit|pediatric check[- ]?up|"
            r"infant growth and development visit)\b",
            re.IGNORECASE,
        ),
        "A child wellness or development visit may be a reason to discuss "
        "Pediatrics as a possible starting point.",
    ),
    (
        "Gynecology",
        re.compile(
            r"\b(?:irregular menstrual periods|irregular periods|"
            r"severe menstrual cramps|painful menstrual cramps|"
            r"menstrual cycle concerns|gynecology follow[- ]?up|"
            r"vaginal discharge)\b",
            re.IGNORECASE,
        ),
        "A menstrual or women's health concern may be a reason to discuss "
        "Gynecology as a possible starting point.",
    ),
    (
        "Ophthalmology",
        re.compile(
            r"\b(?:blurred vision|blurry vision|difficulty seeing clearly|"
            r"eye examination|ophthalmology follow[- ]?up|"
            r"persistent dry eyes)\b",
            re.IGNORECASE,
        ),
        "A vision or eye-care concern may be a reason to discuss "
        "Ophthalmology as a possible starting point.",
    ),
    (
        "Dental",
        re.compile(
            r"\b(?:toothache|tooth pain|pain in (?:my )?tooth|"
            r"gum bleeding|bleeding gums|swollen gums|"
            r"dental check[- ]?up|tooth sensitivity)\b",
            re.IGNORECASE,
        ),
        "A tooth or gum concern may be a reason to discuss "
        "Dental care as a possible starting point.",
    ),
    (
        "ENT",
        re.compile(
            r"\b(?:ear pain|earache|hearing loss|hearing difficulty|"
            r"ringing in (?:my )?ears|persistent sinus congestion|"
            r"recurrent sinus problems|ent follow[- ]?up)\b",
            re.IGNORECASE,
        ),
        "An ear, hearing, or sinus concern may be a reason to discuss "
        "ENT as a possible starting point.",
    ),
    (
        "Gastroenterology",
        re.compile(
            r"\b(?:persistent heartburn|acid reflux|recurrent acid reflux|"
            r"persistent bloating|recurrent bloating|"
            r"gastroenterology follow[- ]?up|digestive health follow[- ]?up)\b",
            re.IGNORECASE,
        ),
        "A recurring digestive concern may be a reason to discuss "
        "Gastroenterology as a possible starting point.",
    ),
    (
        "Urology",
        re.compile(
            r"\b(?:burning when urinating|burning during urination|"
            r"painful urination|pain when urinating|"
            r"frequent urination|urology follow[- ]?up|"
            r"urinary health follow[- ]?up)\b",
            re.IGNORECASE,
        ),
        "A urinary concern may be a reason to discuss "
        "Urology as a possible starting point.",
    ),
    (
        "Psychiatry",
        re.compile(
            r"\b(?:persistent anxiety|frequent panic attacks|"
            r"ongoing anxiety|persistent low mood|"
            r"psychiatry follow[- ]?up|mental health consultation)\b",
            re.IGNORECASE,
        ),
        "A mental wellness concern may be a reason to discuss "
        "Psychiatry as a possible starting point.",
    ),
    (
        "Endocrinology",
        re.compile(
            r"\b(?:thyroid follow[- ]?up|thyroid condition review|"
            r"diabetes follow[- ]?up|blood sugar management|"
            r"endocrinology follow[- ]?up|hormone condition follow[- ]?up)\b",
            re.IGNORECASE,
        ),
        "A thyroid, diabetes, or hormone-care follow-up may be a reason "
        "to discuss Endocrinology as a possible starting point.",
    ),
    (
        "Nephrology",
        re.compile(
            r"\b(?:kidney function follow[- ]?up|kidney disease follow[- ]?up|"
            r"chronic kidney disease review|nephrology follow[- ]?up|"
            r"kidney health follow[- ]?up|protein in (?:my )?urine)\b",
            re.IGNORECASE,
        ),
        "A kidney-health concern may be a reason to discuss "
        "Nephrology as a possible starting point.",
    ),
]


_NEGATION_PATTERN = re.compile(
    r"\b(?:no|not|never|without|deny|denies|"
    r"don't have|do not have|doesn't have|does not have|"
    r"am not experiencing|not experiencing)\b"
    r"(?:[\w\s'-]{0,40})$",
    re.IGNORECASE,
)


def _is_negated(message: str, match_start: int) -> bool:
    """Check whether a nearby negation applies to this symptom phrase."""
    preceding_text = message[max(0, match_start - 55):match_start]
    # Only inspect the current clause, not negations in an earlier sentence.
    preceding_text = re.split(r"[.!?;]", preceding_text)[-1]
    return bool(_NEGATION_PATTERN.search(preceding_text))


def suggest_department(message: str) -> DepartmentSuggestion | None:
    """Return one tentative department suggestion, or None if uncertain."""
    if not isinstance(message, str) or not message.strip():
        return None

    matches: list[tuple[str, str]] = []

    for department, pattern, reason in _SYMPTOM_PATTERNS:
        department_matches = [
            match
            for match in pattern.finditer(message)
            if not _is_negated(message, match.start())
        ]

        if department_matches:
            matches.append((department, reason))

    # Multiple departments, no positive match, or ambiguous wording:
    # do not choose a department automatically.
    if len(matches) != 1:
        return None

    department, reason = matches[0]
    return {
        "department": department,
        "reason": reason,
    }
