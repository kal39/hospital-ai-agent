"""Conservative symptom-to-department suggestions for directory navigation.

This module provides tentative navigation suggestions only.
It does not diagnose, triage, or determine clinical urgency.
Emergency screening must run before this matcher in the agent workflow.
Patient confirmation and consent are required before directory lookup.
"""

import re
from typing import TypedDict


class DepartmentSuggestion(TypedDict):
    department: str
    reason: str


# Specific phrases only. These are navigation patterns, not diagnostic rules.
_SYMPTOM_PATTERNS: list[tuple[str, re.Pattern[str], str]] = [
    (
        "General Medicine",
        re.compile(
            r"\b(?:routine general check[- ]?up|annual physical|"
            r"general health check[- ]?up|general medical consultation|"
            r"general health consultation|primary care consultation|"
            r"general health assessment|routine medical examination)\b",
            re.I,
        ),
        "A general health visit may be a reasonable starting point "
        "for discussing your concern.",
    ),
    (
        "Respiratory Clinic",
        re.compile(
            r"\b(?:persistent|ongoing|recurrent|chronic)\s+cough\b"
            r"|\bcough(?:ing)?\s+(?:for|lasting)\s+(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s+(?:days?|weeks?)\b|\bcough\s+has\s+lasted\s+(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s+(?:days?|weeks?)\b"
            r"|\b(?:recurrent wheezing|recurring wheezing|ongoing wheezing|"
            r"persistent wheezing|asthma follow[- ]?up|asthma review|"
            r"respiratory follow[- ]?up|recurring respiratory problems)\b",
            re.I,
        ),
        "A persistent respiratory concern may be a reason to discuss "
        "the Respiratory Clinic as a possible starting point.",
    ),
    (
        "Cardiology",
        re.compile(
            r"\b(?:heart palpitations|palpitations|irregular heartbeat|"
            r"heartbeat feels irregular|racing heartbeat|"
            r"heart beating irregularly|heart keeps racing|"
            r"heart is racing|fluttering heartbeat|heart fluttering|"
            r"skipped heartbeats|irregular heart rhythm|"
            r"palpitations follow[- ]?up|cardiology follow[- ]?up)\b",
            re.I,
        ),
        "A heart-rhythm concern may be a reason to discuss "
        "Cardiology as a possible starting point.",
    ),
    (
        "Dermatology",
        re.compile(
            r"\b(?:skin rash|itchy rash|rash on (?:my )?skin|"
            r"eczema|acne|persistent itching|hair loss|nail changes|"
            r"hives|skin irritation|recurring rash|dry skin condition|"
            r"scalp problem|persistent acne|dermatology follow[- ]?up)\b",
            re.I,
        ),
        "A skin, hair, or nail concern may be a reason to discuss "
        "Dermatology as a possible starting point.",
    ),
    (
        "Neurology",
        re.compile(
            r"\b(?:recurrent migraine|migraine attacks|migraine follow[- ]?up|"
            r"recurrent headaches|recurring headaches|"
            r"recurrent numbness|numbness in (?:my )?(?:hands?|feet|arms?|legs?)|"
            r"tingling in (?:my )?(?:hands?|feet|arms?|legs?)|"
            r"hand tremor|recurring tremors|persistent tremor|"
            r"uncontrolled shaking|neurology follow[- ]?up)\b",
            re.I,
        ),
        "A recurring neurological concern may be a reason to discuss "
        "Neurology as a possible starting point.",
    ),
    (
        "Orthopedics",
        re.compile(
            r"\b(?:knee joint pain|hip joint pain|shoulder joint pain|"
            r"joint pain|pain in (?:my )?(?:knee|hip|shoulder|elbow|ankle)|"
            r"joint swelling|recurrent joint pain|joint stiffness|joints? feel stiff|"
            r"persistent back pain|musculoskeletal follow[- ]?up|"
            r"orthopedic follow[- ]?up|sports injury follow[- ]?up)\b",
            re.I,
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
            r"infant growth and development visit|child health assessment|"
            r"infant check[- ]?up|infant needs (?:a )?check[- ]?up|child growth monitoring|"
            r"child development assessment|child needs (?:a )?development assessment|childhood wellness visit|"
            r"pediatric wellness visit)\b",
            re.I,
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
            r"vaginal discharge|missed periods|changes in (?:my )?menstrual cycles|"
            r"painful periods|menstrual health consultation|"
            r"women's health check[- ]?up|womens health check[- ]?up|"
            r"gynecological consultation)\b",
            re.I,
        ),
        "A menstrual or women's health concern may be a reason to discuss "
        "Gynecology as a possible starting point.",
    ),
    (
        "Ophthalmology",
        re.compile(
            r"\b(?:blurred vision|blurry vision|difficulty seeing clearly|"
            r"eye examination|eye exam|ophthalmology follow[- ]?up|"
            r"persistent dry eyes|eye redness|red eyes|eye irritation|"
            r"watery eyes|eyes are watery|eye discomfort|vision assessment|"
            r"vision examination)\b",
            re.I,
        ),
        "A vision or eye-care concern may be a reason to discuss "
        "Ophthalmology as a possible starting point.",
    ),
    (
        "Dental",
        re.compile(
            r"\b(?:toothache|tooth pain|pain in (?:my )?tooth|"
            r"gum bleeding|bleeding gums|gums? (?:are )?bleeding|"
            r"swollen gums|dental check[- ]?up|tooth sensitivity|"
            r"tooth decay|cavities|gum discomfort|dental cleaning|"
            r"broken tooth|dental examination|dental follow[- ]?up)\b",
            re.I,
        ),
        "A tooth or gum concern may be a reason to discuss "
        "Dental care as a possible starting point.",
    ),
    (
        "ENT",
        re.compile(
            r"\b(?:ear pain|earache|hearing loss|hearing difficulty|"
            r"ringing in (?:my )?ears|persistent sinus congestion|"
            r"recurrent sinus problems|ent follow[- ]?up|"
            r"sore throat|tonsil concerns|tonsil problems|"
            r"nasal congestion|recurring ear infections|"
            r"hearing assessment|sinus problems|persistent sore throat)\b",
            re.I,
        ),
        "An ear, hearing, throat, or sinus concern may be a reason to discuss "
        "ENT as a possible starting point.",
    ),
    (
        "Gastroenterology",
        re.compile(
            r"\b(?:persistent heartburn|acid reflux|recurrent acid reflux|"
            r"persistent bloating|recurrent bloating|"
            r"gastroenterology follow[- ]?up|digestive health follow[- ]?up|"
            r"persistent constipation|recurring constipation|"
            r"persistent diarrhea|recurring diarrhea|"
            r"digestive discomfort|recurring abdominal bloating|"
            r"nausea follow[- ]?up|persistent indigestion|"
            r"gastrointestinal follow[- ]?up)\b",
            re.I,
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
            r"urinary health follow[- ]?up|urinary urgency|"
            r"difficulty urinating|urinary health consultation|"
            r"urinary frequency|urological consultation)\b",
            re.I,
        ),
        "A urinary concern may be a reason to discuss "
        "Urology as a possible starting point.",
    ),
    (
        "Psychiatry",
        re.compile(
            r"\b(?:persistent anxiety|frequent panic attacks|"
            r"ongoing anxiety|persistent low mood|"
            r"psychiatry follow[- ]?up|mental health consultation|"
            r"persistent stress|ongoing stress|recurring panic attacks|"
            r"depression follow[- ]?up|mental wellness assessment|"
            r"mental wellness consultation)\b",
            re.I,
        ),
        "A mental wellness concern may be a reason to discuss "
        "Psychiatry as a possible starting point.",
    ),
    (
        "Endocrinology",
        re.compile(
            r"\b(?:thyroid follow[- ]?up|thyroid condition review|"
            r"diabetes follow[- ]?up|blood sugar management|"
            r"endocrinology follow[- ]?up|hormone condition follow[- ]?up|"
            r"thyroid review|hormone imbalance follow[- ]?up|"
            r"diabetes management|blood sugar review|"
            r"endocrine consultation)\b",
            re.I,
        ),
        "A thyroid, diabetes, or hormone-care follow-up may be a reason "
        "to discuss Endocrinology as a possible starting point.",
    ),
    (
        "Nephrology",
        re.compile(
            r"\b(?:kidney function follow[- ]?up|kidney disease follow[- ]?up|"
            r"chronic kidney disease review|nephrology follow[- ]?up|"
            r"kidney health follow[- ]?up|protein in (?:my )?urine|"
            r"proteinuria follow[- ]?up|reduced kidney function review|"
            r"kidney health assessment|chronic kidney disease follow[- ]?up)\b",
            re.I,
        ),
        "A kidney-health concern may be a reason to discuss "
        "Nephrology as a possible starting point.",
    ),
]


_NEGATION_PATTERN = re.compile(
    r"\b(?:no|not|never|without|deny|denies|"
    r"don't have|do not have|doesn't have|does not have|"
    r"am not experiencing|not experiencing|"
    r"haven't had|have not had)\b"
    r"(?:[\w\s'-]{0,45})$",
    re.I,
)


def _is_negated(message: str, match_start: int) -> bool:
    """Check whether a nearby negation applies to a matched phrase."""
    preceding = message[max(0, match_start - 60):match_start]
    preceding = re.split(r"[.!?;]", preceding)[-1]
    return bool(_NEGATION_PATTERN.search(preceding))


# Common symptoms that are too broad to route by themselves.
# If one occurs alongside a specific match, it blocks automatic suggestion
# unless that exact symptom phrase is covered by a recognized pattern.
_OTHER_SYMPTOM_MENTIONS = re.compile(
    r"\b(?:cough|coughing|headache|headaches|dizziness|dizzy|"
    r"stomach discomfort|stomach pain|abdominal pain|"
    r"fever|back pain|chest pain|difficulty breathing|"
    r"shortness of breath|breathlessness|weakness|fatigue|"
    r"nausea|vomiting|diarrhea|constipation|sore throat|"
    r"runny nose|body aches|pain|swelling|rash)\b",
    re.I,
)


# Defense in depth only. The agent's emergency safety screening must run first.
_POTENTIALLY_URGENT_MENTIONS = re.compile(
    r"\b(?:chest pain|chest pressure|severe difficulty breathing|"
    r"cannot breathe|can't breathe|severe shortness of breath|"
    r"sudden vision loss|sudden blindness|suddenly lost (?:my )?vision|sudden loss of vision|"
    r"sudden weakness on one side|face drooping|"
    r"slurred speech|sudden confusion|"
    r"unconscious|loss of consciousness|"
    r"severe bleeding|coughing blood)\b",
    re.I,
)


def suggest_department(message: str) -> DepartmentSuggestion | None:
    """Return one tentative department suggestion, or None if uncertain."""
    if not isinstance(message, str) or not message.strip():
        return None

    # Never make an ordinary directory suggestion for potentially urgent text.
    if any(
        not _is_negated(message, match.start())
        for match in _POTENTIALLY_URGENT_MENTIONS.finditer(message)
    ):
        return None

    matches: list[tuple[str, str]] = []
    recognized_spans: list[tuple[int, int]] = []

    for department, pattern, reason in _SYMPTOM_PATTERNS:
        department_matches = [
            match for match in pattern.finditer(message)
            if not _is_negated(message, match.start())
        ]

        if department_matches:
            matches.append((department, reason))
            recognized_spans.extend(
                (match.start(), match.end())
                for match in department_matches
            )

    # Do not ignore an additional broad symptom merely because another
    # phrase happens to match a department.
    for other_match in _OTHER_SYMPTOM_MENTIONS.finditer(message):
        if _is_negated(message, other_match.start()):
            continue

        covered = any(
            start <= other_match.start() and end >= other_match.end()
            for start, end in recognized_spans
        )
        if not covered:
            return None

    # Multiple departments or no positive match means no recommendation.
    if len(matches) != 1:
        return None

    department, reason = matches[0]
    return {"department": department, "reason": reason}



def suggest_department_or_general_medicine(
    message: str,
) -> DepartmentSuggestion | None:
    """Suggest a clear department, or General Medicine when uncertain.

    Potentially urgent symptoms are deliberately excluded from routine
    department navigation. This function is for appointment guidance,
    not diagnosis or clinical triage.
    """
    if not isinstance(message, str) or not message.strip():
        return None

    # Preserve the emergency safeguard before applying any fallback.
    if any(
        not _is_negated(message, match.start())
        for match in _POTENTIALLY_URGENT_MENTIONS.finditer(message)
    ):
        return None

    has_symptom_mention = any(
        not _is_negated(message, match.start())
        for match in _OTHER_SYMPTOM_MENTIONS.finditer(message)
    ) or any(
        not _is_negated(message, match.start())
        for _, pattern, _ in _SYMPTOM_PATTERNS
        for match in pattern.finditer(message)
    )

    if not has_symptom_mention:
        return None

    suggestion = suggest_department(message)
    if suggestion is not None:
        return suggestion

    return {
        "department": "General Medicine",
        "reason": (
            "No single suitable specialist department could be identified "
            "from your message. General Medicine may be a reasonable "
            "starting point for discussing your concern with a clinician."
        ),
    }
