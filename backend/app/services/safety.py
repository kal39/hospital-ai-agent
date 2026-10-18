
"""Bilingual safety checks for potentially urgent medical requests.

These keyword rules are prototype safeguards, not a clinical triage system.
Amharic patterns and messages require review by a qualified clinician.
"""

import re
from typing import TypedDict


class SafetyResult(TypedDict):
    blocked: bool
    urgent: bool
    message: str | None


def _compile_patterns(patterns: list[str]) -> list[re.Pattern[str]]:
    return [re.compile(pattern, re.IGNORECASE) for pattern in patterns]


def _matches(patterns: list[re.Pattern[str]], message: str) -> bool:
    return any(pattern.search(message) for pattern in patterns)


UNSAFE_PATTERNS = _compile_patterns(
    [
        r"\bshould\s+i\s+stop\s+taking\b",
        r"\bshould\s+i\s+stop\s+my\s+medication\b",
        r"\bchange\s+my\s+medication\b",
        r"\bincrease\s+my\s+dose\b",
        r"\bdecrease\s+my\s+dose\b",
        r"\bwhat\s+dose\s+should\s+i\s+take\b",
        r"\bprescribe\s+(?:me|a|an|some)\b",
    ]
)

URGENT_PATTERNS = _compile_patterns(
    [
        r"\bchest pain\b",
        r"\bdifficulty breathing\b",
        r"\bshortness of breath\b",
        r"\bcan'?t breathe\b",
        r"\bcannot breathe\b",
        r"\bsevere bleeding\b",
        r"\bunconscious\b",
        r"\bloss of consciousness\b",
        r"\bsevere allergic reaction\b",
        r"የደረት\s*ህመም",
        r"የደረት\s*ሕመም",
        r"የመተንፈስ\s*ችግር",
        r"መተንፈስ\s*አልቻልኩም",
        r"ከባድ\s*ደም\s*መፍሰስ",
    ]
)

KIDNEY_OR_BACK_PATTERNS = _compile_patterns(
    [
        r"\b(?:kidney|kidneys|flank|lower back)\b",
        r"ኩላሊ",  # Covers forms such as ኩላሊቴ and ኩላሊት
        r"ጀርባ",
        r"ወገብ",
    ]
)

PAIN_PATTERNS = _compile_patterns(
    [
        r"\b(?:pain|ache|aching|hurts?|hurt|sore)\b",
        r"ህመም",
        r"ሕመም",
        r"ያማል",
        r"ያመኛል",
    ]
)

URINARY_PATTERNS = _compile_patterns(
    [
        r"\b(?:frequent(?:ly)?|often|more often)\b.{0,40}"
        r"\b(?:urination|urinating|urinate|pee|peeing|urine|bathroom)\b",
        r"\b(?:urination|urinating|urinate|pee|peeing)\b.{0,35}"
        r"\b(?:often|frequently|more|a lot|all the time)\b",
        r"\b(?:burning|painful)\b.{0,25}"
        r"\b(?:urination|urinating|pee|peeing)\b",
        r"\bblood in (?:my )?(?:urine|pee)\b",
        r"\bunable to urinate\b",
        r"\bcannot urinate\b",
        r"\bhaven'?t urinated all day\b",
        r"\bnot passed urine all day\b",
        r"በሽንት.{0,20}(?:ደም|ህመም|ሕመም)",
        r"ሽንት.{0,25}(?:ያማል|ህመም|ሕመም)",
        r"ብዙ\s*ጊዜ.{0,20}ሽንት",
        r"ያስቸገረኛል",
        r"ቶሎ\s*ቶሎ",
    ]
)

URGENT_MESSAGE_EN = (
    "Your message may describe a medical emergency. Please seek immediate "
    "medical attention or contact your local emergency service. I cannot "
    "assess emergencies or replace a qualified clinician."
)

URGENT_MESSAGE_AM = (
    "መልዕክትዎ አስቸኳይ የሕክምና ችግርን ሊያመለክት ይችላል። "
    "እባክዎ ወዲያውኑ የሕክምና እርዳታ ያግኙ ወይም የአካባቢዎን "
    "የአስቸኳይ አገልግሎት ያነጋግሩ።"
)

UNSAFE_MESSAGE_EN = (
    "I can explain information already present in your hospital records, "
    "but I cannot recommend independently starting, stopping, or changing "
    "medication. Please discuss medication decisions with your care team."
)

UNSAFE_MESSAGE_AM = (
    "በሆስፒታልዎ መዝገብ ውስጥ ያለውን መረጃ ማብራራት እችላለሁ። "
    "ሆኖም መድኃኒት መጀመር፣ ማቆም ወይም መጠኑን መቀየር "
    "አልመክርም። እባክዎ ይህንን ከሕክምና ቡድንዎ ጋር ይወያዩ።"
)

KIDNEY_URINARY_MESSAGE_EN = (
    "Pain around the kidney area, back, or side together with urinary "
    "symptoms should be assessed by a healthcare professional promptly, "
    "preferably today. These symptoms can have several causes, and I "
    "cannot determine the cause here. Seek urgent medical care now if you "
    "also have fever or chills, vomiting, blood in your urine, severe or "
    "worsening pain, confusion, or difficulty passing urine. An earlier "
    "normal creatinine result does not rule out a current problem."
)

KIDNEY_URINARY_MESSAGE_AM = (
    "በኩላሊት፣ በጀርባ ወይም በጎን አካባቢ ህመም ከሽንት ችግር ጋር "
    "ከተከሰተ ዛሬውኑ የጤና ባለሙያን ያነጋግሩ። "
    "ትኩሳት፣ ማስታወክ፣ በሽንት ውስጥ ደም፣ ከባድ ወይም እየባሰ የሚሄድ "
    "ህመም፣ ግራ መጋባት ወይም ሽንት ማስወጣት መቸገር ካለ "
    "ወዲያውኑ አስቸኳይ የሕክምና እርዳታ ያግኙ።"
)


def evaluate_safety(message: str, language: str = "en") -> SafetyResult:
    """Check urgent, kidney/urinary, then restricted medication requests."""
    selected_language = "am" if language == "am" else "en"

    if _matches(URGENT_PATTERNS, message):
        return {
            "blocked": True,
            "urgent": True,
            "message": (
                URGENT_MESSAGE_AM
                if selected_language == "am"
                else URGENT_MESSAGE_EN
            ),
        }

    kidney_or_back_pain = (
        _matches(KIDNEY_OR_BACK_PATTERNS, message)
        and _matches(PAIN_PATTERNS, message)
    )
    urinary_symptoms = _matches(URINARY_PATTERNS, message)

    if kidney_or_back_pain and urinary_symptoms:
        return {
            "blocked": True,
            "urgent": False,
            "message": (
                KIDNEY_URINARY_MESSAGE_AM
                if selected_language == "am"
                else KIDNEY_URINARY_MESSAGE_EN
            ),
        }

    if _matches(UNSAFE_PATTERNS, message):
        return {
            "blocked": True,
            "urgent": False,
            "message": (
                UNSAFE_MESSAGE_AM
                if selected_language == "am"
                else UNSAFE_MESSAGE_EN
            ),
        }

    return {
        "blocked": False,
        "urgent": False,
        "message": None,
    }
