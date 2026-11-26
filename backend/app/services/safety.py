
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


def _matches_urgent(message: str) -> bool:
    """Match potentially current urgent symptoms, respecting negation and history."""
    contrast_pattern = re.compile(
        r"\b(?:but|however|although|though|yet|except)\b",
        re.IGNORECASE,
    )
    clause_boundary_pattern = re.compile(
        r"[.!?;]|,\s*(?=(?:and|now|currently|at\s+present)\b)"
        r"|\b(?:but|however|although|though|yet|except)\b",
        re.IGNORECASE,
    )
    negation_pattern = re.compile(
        r"\b(?:no|without|denies|denied|"
        r"don't\s+have|do\s+not\s+have|"
        r"doesn't\s+have|does\s+not\s+have|"
        r"haven't\s+had|have\s+not\s+had|"
        r"never\s+had|"
        r"did\s+not|didn\x27t|"
        r"not\s+(?:currently\s+)?"
        r"(?:experiencing|having|feeling|suffering\s+from))\b",
        re.IGNORECASE,
    )
    historical_time_pattern = re.compile(
        r"\b(?:yesterday|last\s+night|last\s+week|"
        r"last\s+month|last\s+year|"
        r"many\s+years\s+ago|"
        r"\d+\s+(?:minutes?|hours?|days?|weeks?|months?|years?)\s+ago)\b",
        re.IGNORECASE,
    )
    ongoing_pattern = re.compile(
        r"\b(?:still\s+(?:have|having|feel|feeling|experience|experiencing|"
        r"happening|occurring)|"
        r"continues?\s+to\s+(?:hurt|happen|occur|bleed)|"
        r"has\s+not\s+stopped|have\s+not\s+stopped|"
        r"is\s+still\s+(?:happening|occurring|bleeding)|"
        r"since\s+(?:yesterday|last\s+(?:night|week|month|year)))\b",
        re.IGNORECASE,
    )
    resolution_pattern = re.compile(
        r"\b(?:went\s+away|has\s+gone\s+away|"
        r"has\s+(?:completely\s+)?stopped|"
        r"have\s+(?:completely\s+)?stopped|"
        r"has\s+resolved|is\s+resolved|"
        r"completely\s+resolved|"
        r"no\s+longer\s+(?:have|feel|experience)|"
        r"(?:has|have|had)\s+not\s+returned|"
        r"(?:hasn't|haven't|hadn't)\s+returned|"
        r"did\s+not\s+return|didn't\s+return|"
        r"feels?\s+fine\s+now|"
        r"symptoms?\s+(?:are\s+)?gone)\b",
        re.IGNORECASE,
    )
    recurrence_pattern = re.compile(
        r"\b(?:came\s+back|has\s+returned|returned|"
        r"started\s+again|happening\s+again|"
        r"pain\s+again|symptoms?\s+(?:have\s+)?returned)\b",
        re.IGNORECASE,
    )
    nonrecurrence_pattern = re.compile(
        r"\b(?:(?:has|have|had)\s+not\s+returned|"
        r"(?:hasn't|haven't|hadn't)\s+returned|"
        r"did\s+not\s+return|didn't\s+return)\b",
        re.IGNORECASE,
    )

    for pattern in URGENT_PATTERNS:
        for match in pattern.finditer(message):
            clause_start = 0
            clause_end = len(message)

            for boundary in clause_boundary_pattern.finditer(message):
                if boundary.end() <= match.start():
                    clause_start = boundary.end()
                elif boundary.start() >= match.end():
                    clause_end = boundary.start()
                    break

            clause = message[clause_start:clause_end]
            relative_match_start = match.start() - clause_start
            relative_match_end = match.end() - clause_start

            prefix = clause[:relative_match_start]
            suffix = clause[relative_match_end:]

            if re.search(r"\bnot\s+only\b", prefix, re.IGNORECASE):
                prefix = re.sub(
                    r"\bnot\s+only\b",
                    "",
                    prefix,
                    flags=re.IGNORECASE,
                )

            if negation_pattern.search(prefix):
                continue

            historical = bool(historical_time_pattern.search(clause))
            ongoing = bool(ongoing_pattern.search(clause))

            # Check the remainder of the sentence, including after contrast
            # words such as "but", for explicit resolution or recurrence.
            sentence_end = len(message)
            for punctuation_char in ".!?;":
                position = message.find(punctuation_char, match.end())
                if position >= 0:
                    sentence_end = min(sentence_end, position)

            sentence_suffix = message[match.end():sentence_end]
            resolved = bool(resolution_pattern.search(sentence_suffix))
            recurring = (
                bool(recurrence_pattern.search(sentence_suffix))
                and not bool(nonrecurrence_pattern.search(sentence_suffix))
            )

            # Also recognize recurrence when resolution and return are
            # described together in a following sentence.
            following_sentences = re.split(
                r"[.!?;]",
                message[match.end():],
            )

            resolved_then_recurring = False

            for following_sentence in following_sentences:
                # Accept either a pronoun reference or an explicit restatement
                # of the original symptom. This prevents unrelated symptoms
                # from being associated with the earlier urgent symptom.
                matched_symptom = re.sub(
                    r"^\s*(?:suddenly\s+)?"
                    r"(?:have|has|had|having|developed|develop)\s+",
                    "",
                    match.group(0),
                    flags=re.IGNORECASE,
                ).strip()

                pronoun_reference = bool(
                    re.match(
                        r"\s*(?:it|they|these symptoms|those symptoms|"
                        r"the symptoms?)\b",
                        following_sentence,
                        re.IGNORECASE,
                    )
                )

                explicit_symptom_reference = bool(
                    matched_symptom
                    and re.search(
                        rf"\b{re.escape(matched_symptom)}\b",
                        following_sentence,
                        re.IGNORECASE,
                    )
                )

                refers_to_previous_symptom = (
                    pronoun_reference or explicit_symptom_reference
                )

                if not refers_to_previous_symptom:
                    continue

                resolution_match = resolution_pattern.search(
                    following_sentence
                )

                if not resolution_match:
                    continue

                recurrence_match = recurrence_pattern.search(
                    following_sentence,
                    resolution_match.end(),
                )

                if (
                    recurrence_match
                    and not nonrecurrence_pattern.search(following_sentence)
                ):
                    resolved_then_recurring = True
                    break

            recurring = recurring or resolved_then_recurring

            if historical and not ongoing and not recurring:
                continue

            if resolved and not ongoing and not recurring:
                continue

            return True

    return False

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
        r"\bgasping\s+for\s+air\b",
        r"\bstruggling\s+to\s+breathe\b",
        r"\bcan'?t breathe\b",
        r"\bcannot breathe\b",
        r"\bsevere bleeding\b",
        r"\bunconscious\b",
        r"\bloss of consciousness\b",
        r"\bsevere allergic reaction\b",
        # Additional breathing emergency descriptions
        r"\b(?:my\s+)?breathing\s+(?:is\s+)?(?:getting|becoming)\s+worse\b",
        r"\bcan(?:not|'t)\s+catch\s+(?:(?:my|his|her|their)\s+)?breath\b",
        r"\bstruggling\s+to\s+catch\s+(?:(?:my|his|her|their)\s+)?breath\b",
        r"\b(?:becoming|getting)\s+(?:more\s+and\s+more\s+)?breathless\b",
        # Additional possible stroke symptoms
        r"\bone\s+side\s+of\s+(?:my|his|her|their|the)\s+face\s+(?:suddenly\s+)?(?:feels?\s+)?numb\b",
        r"\b(?:(?:my|his|her|their)\s+)?(?:(?:right|left)\s+)?(?:arm|leg)\s+(?:suddenly\s+)?(?:went|became|feels?|is)\s+weak\b",
        r"\b(?:(?:my|his|her|their)\s+)?(?:right|left)\s+(?:arm|leg)\s+(?:suddenly\s+)?(?:went|became|feels?|is)\s+numb\b",
        r"\bone\s+side\s+of\s+(?:my|his|her|their|the)\s+(?:body|face)\s+(?:feels?|became|is)\s+numb\b",
        # Additional possible severe allergic reaction symptoms
        r"\bthroat\s+(?:is\s+)?closing(?:\s+up)?\b",
        r"\b(?:my|his|her|their)\s+lips?\s+(?:are\s+)?swelling\b",
        r"\bswelling\s+of\s+(?:my|his|her|their)\s+lips?\b",
        r"\bswollen\s+lips?\b",
        # Other potentially life-threatening symptoms
        r"\b(?:vomiting|throwing\s+up)\s+blood\b",
        r"\bstopped\s+breathing\b",
        # Possible cardiac emergency symptoms
        r"\b(?:having\s+a\s+)?heart\s+attack\b",
        r"\bchest\s+(?:pressure|tightness|squeezing)\b",
        r"\bpressure\s+in\s+(?:my|the)\s+chest\b",
        r"\btightness\s+in\s+(?:my|the)\s+chest\b",
        # Possible stroke symptoms
        r"\b(?:one\s+side\s+of\s+(?:my|the)\s+)?(?:body|arm|leg)\s+(?:suddenly\s+)?(?:became\s+)?weak\b",
        r"\b(?:facial|face)\s+droop(?:ing)?\b",
        r"\b(?:one\s+side\s+of\s+(?:my|the)\s+)?face\s+is\s+drooping\b",
        r"\bslurred\s+speech\b",
        r"\b(?:sudden\s+)?difficulty\s+speaking\b",
        r"\btrouble\s+speaking\b",
        r"\bcannot\s+speak\s+(?:clearly|properly)\b",
        r"\b(?:suddenly\s+)?(?:can\x27t|cannot|can\s+not)\s+get\s+(?:my|his|her|their)\s+words\s+out\b",
        r"\b(?:my|his|her|their)\s+speech\s+(?:suddenly\s+)?(?:became|sounds?|is)\s+(?:garbled|unclear|incoherent)\b",
        r"\b(?:suddenly\s+(?:became|become|felt|feel|am)\s+confused|sudden\s+confusion)\b",
        r"\bsuddenly\s+(?:cannot|can\x27t|can\s+not)\s+understand\s+(?:what\s+)?(?:people|someone|others)\s+(?:are\s+)?saying\b",
        r"\bsuddenly\s+(?:cannot|can\x27t|can\s+not)\s+walk\s+straight\b",
        r"\bsuddenly\s+(?:lost|lose)\s+(?:my\s+)?balance\b",
        r"\bsuddenly\s+(?:have|has|had|having|developed|develop)\s+double\s+vision\b",
        r"\bsuddenly\s+(?:cannot|can\x27t|can\s+not)\s+swallow(?:\s+properly)?\b",
        r"\bsuddenly\s+(?:feel|felt|become|became)\s+(?:severely\s+)?dizzy\b",
        r"\bsuddenly\s+(?:cannot|can\x27t|can\s+not)\s+stay\s+upright\b",
        r"\b(?:sudden\s+)?loss\s+of\s+(?:vision|sight)\s+in\s+(?:(?:my|his|her|their)\s+)?(?:one|right|left)\s+eye\b",
        r"\b(?:suddenly\s+)?(?:lost|lose)\s+(?:my|his|her|their\s+)?(?:vision|sight)\s+in\s+(?:(?:my|his|her|their)\s+)?(?:one|right|left)\s+eye\b",
        r"\b(?:suddenly\s+)?(?:went\s+)?blind\s+in\s+(?:(?:my|his|her|their)\s+)?(?:one|right|left)\s+eye\b",
        r"\b(?:can\x27t|cannot|can\s+not)\s+see\s+out\s+of\s+(?:(?:my|his|her|their)\s+)?(?:one|right|left)\s+eye\b",
        r"\b(?:worst|most\s+severe)\s+headache\s+of\s+my\s+life\b",
        # Seizures and convulsions
        r"\b(?:having\s+a\s+)?seizure\b",
        r"\bconvulsions?\b",
        r"\bconvulsing\b",
        # Severe bleeding
        r"\bheavy\s+bleeding\b",
        r"\bbleeding\s+heavily\b",
        r"\bbleeding\s+(?:that\s+)?(?:won't|will\s+not|doesn't|does\s+not)\s+stop\b",
        r"\bbleeding\s+profusely\b",
        # Collapse and unresponsiveness
        r"\b(?:suddenly\s+)?collapsed\b",
        r"\b(?:fainted|fainting|pass(?:ed|ing)\s+out)\b",
        r"\bunresponsive\b",
        r"\bnot\s+responding\b",
        # Possible severe allergic reaction symptoms
        r"\btongue\s+(?:is\s+)?swelling\b",
        r"\bswollen\s+tongue\b",
        r"\bswelling\s+of\s+(?:my|the)\s+tongue\b",
        # Possible medication overdose or poisoning
        r"\b(?:accidentally\s+)?took\s+too\s+many\s+(?:tablets|pills|medications?)\b",
        r"\b(?:accidentally\s+)?taken\s+too\s+many\s+(?:tablets|pills|medications?)\b",
        r"\b(?:accidentally\s+)?took\s+too\s+much\s+(?:medication|medicine|of\s+my\s+medication)\b",
        r"\bmedication\s+overdose\b",
        r"\bdrug\s+overdose\b",
        r"\boverdosed\b",
        r"\bpoison(?:ed|ing)?\b",
        'የደረት\\s*ህመም',
        'የደረት\\s*ሕመም',
        'የመተንፈስ\\s*ችግር',
        'መተንፈስ\\s*አልቻልኩም',
        'ከባድ\\s*ደም\\s*መፍሰስ',
    ]
)

KIDNEY_OR_BACK_PATTERNS = _compile_patterns(
    [
        r"\b(?:kidney|kidneys|flank|lower back)\b",
        'ኩላሊ',  # Covers forms such as áŠ©áˆ‹áˆŠá‰´ and áŠ©áˆ‹áˆŠá‰µ
        'ጀርባ',
        'ወገብ',
    ]
)

PAIN_PATTERNS = _compile_patterns(
    [
        r"\b(?:pain|ache|aching|hurts?|hurt|sore)\b",
        'ህመም',
        'ሕመም',
        'ያማል',
        'ያመኛል',
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
        'በሽንት.{0,20}(?:ደም|ህመም|ሕመም)',
        'ሽንት.{0,25}(?:ያማል|ህመም|ሕመም)',
        'ብዙ\\s*ጊዜ.{0,20}ሽንት',
        'ያስቸገረኛል',
        'ቶሎ\\s*ቶሎ',
    ]
)

URGENT_MESSAGE_EN = (
    "Your message may describe a medical emergency. Please seek immediate "
    "medical attention or contact your local emergency service. I cannot "
    "assess emergencies or replace a qualified clinician."
)

URGENT_MESSAGE_AM = (
    'መልዕክትዎ አስቸኳይ የሕክምና ችግርን ሊያመለክት ይችላል። '
    'እባክዎ ወዲያውኑ የሕክምና እርዳታ ያግኙ ወይም የአካባቢዎን '
    'የአስቸኳይ አገልግሎት ያነጋግሩ።'
)

DIZZINESS_PATTERNS = _compile_patterns(
    [
        r"\b(?:dizz(?:y|iness)|lightheaded|light-headed|feeling faint)\b",
        'ማዞር',
        'ዞረኝ',
        'ይዞረኛል',
        'ራሴ\\s*ዞረ',
        'ራስ\\s*ማዞር',
    ]
)

DIZZINESS_MESSAGE_EN = (
    "Dizziness can have several causes and should be assessed by a "
    "healthcare professional. Please contact your care team promptly, "
    "especially if this is new or recurring. Do not drive while dizzy; "
    "sit or lie down to reduce the risk of falling. If you develop "
    "fainting, chest pain, difficulty breathing, new weakness, trouble "
    "speaking, or severe or rapidly worsening symptoms, seek emergency "
    "medical care now."
)

DIZZINESS_MESSAGE_AM = (
    'ማዞር እያጋጠመዎት ከሆነ እናዝናለን። መድኃኒት ከወሰዱ በኋላ '
    'የሚከሰት ማዞር የተለያዩ ምክንያቶች ሊኖሩት ይችላሉ። '
    'በተለይ አዲስ ከሆነ ወይም በተደጋጋሚ ከተከሰተ፣ በቅርቡ '
    'ከጤና ቡድንዎ ጋር ይገናኙ። ማዞር እያለብዎት መኪና '
    'አይንዱ፤ ከመውደቅ ለመከላከል ይቀመጡ ወይም ይተኙ። '
    'በዚህ ውይይት ተመስርተው መድኃኒትዎን በራስዎ አይቀይሩ። '
    'ከሳቱ፣ የደረት ህመም፣ የመተንፈስ ችግር፣ አዲስ የአካል '
    'ድክመት፣ የመናገር ችግር ወይም ከባድና በፍጥነት እየባሰ '
    'የሚሄድ ምልክት ካለ ወዲያውኑ አስቸኳይ የሕክምና '
    'እርዳታ ያግኙ።'
)
UNSAFE_MESSAGE_EN = (
    "I can explain information already present in your hospital records, "
    "but I cannot recommend independently starting, stopping, or changing "
    "medication. Please discuss medication decisions with your care team."
)

UNSAFE_MESSAGE_AM = (
    'በሆስፒታልዎ መዝገብ ውስጥ ያለውን መረጃ ማብራራት እችላለሁ። '
    'ሆኖም መድኃኒት መጀመር፣ ማቆም ወይም መጠኑን መቀየር '
    'አልመክርም። እባክዎ ይህንን ከሕክምና ቡድንዎ ጋር ይወያዩ።'
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
    'በኩላሊት፣ በጀርባ ወይም በጎን አካባቢ ህመም ከሽንት ችግር ጋር '
    'ከተከሰተ ዛሬውኑ የጤና ባለሙያን ያነጋግሩ። '
    'ትኩሳት፣ ማስታወክ፣ በሽንት ውስጥ ደም፣ ከባድ ወይም እየባሰ የሚሄድ '
    'ህመም፣ ግራ መጋባት ወይም ሽንት ማስወጣት መቸገር ካለ '
    'ወዲያውኑ አስቸኳይ የሕክምና እርዳታ ያግኙ።'
)


def suggest_care_case_priority(
    message: str,
    language: str = "en",
) -> dict[str, str]:
    """Return a prototype staff-routing suggestion, not clinical triage."""
    selected_language = "am" if language == "am" else "en"

    if _matches_urgent(message):
        reason = (
            "An existing emergency symptom rule matched this concern. "
            "This is an automated routing suggestion, not a clinical assessment."
            if selected_language == "en"
            else "\u12ed\u1205 \u1218\u120d\u12d5\u12ad\u1275 \u12a8\u12a0\u1235\u1278\u12b3\u12ed \u121d\u120d\u12ad\u1276\u127d \u130b\u122d \u12e8\u121a\u12db\u1218\u12f5 \u12e8\u12f0\u1205\u1295\u1290\u1275 \u1215\u130d \u12a0\u1235\u1290\u1235\u1277\u120d\u1362 \u12ed\u1205 \u1260\u122b\u1235-\u1230\u122d \u12e8\u1270\u12f0\u1228\u1308 \u12e8\u121b\u1235\u1270\u120b\u1208\u134a\u12eb \u1325\u1246\u121b \u1290\u12cd\u1364 \u12e8\u1215\u12ad\u121d\u1293 \u130d\u121d\u1308\u121b \u12a0\u12ed\u12f0\u1208\u121d\u1362"
        )
        return {
            "prioritySuggestion": "emergency",
            "priorityReason": reason,
        }

    kidney_or_back_pain = (
        _matches(KIDNEY_OR_BACK_PATTERNS, message)
        and _matches(PAIN_PATTERNS, message)
    )
    urinary_symptoms = _matches(URINARY_PATTERNS, message)
    dizziness = _matches(DIZZINESS_PATTERNS, message)

    if (kidney_or_back_pain and urinary_symptoms) or dizziness:
        reason = (
            "An existing safety advisory recommends prompt contact "
            "with the care team. This is an automated routing suggestion, "
            "not a clinical assessment."
            if selected_language == "en"
            else "\u12eb\u1208\u12cd \u12e8\u12f0\u1205\u1295\u1290\u1275 \u121d\u12ad\u122d \u12a8\u1324\u1293 \u1261\u12f5\u1291 \u130b\u122d \u1260\u1245\u122d\u1261 \u12a5\u1295\u12f2\u1308\u1293\u1299 \u12ed\u1218\u12ad\u122b\u120d\u1362 \u12ed\u1205 \u1260\u122b\u1235-\u1230\u122d \u12e8\u1270\u12f0\u1228\u1308 \u12e8\u121b\u1235\u1270\u120b\u1208\u134a\u12eb \u1325\u1246\u121b \u1290\u12cd\u1364 \u12e8\u1215\u12ad\u121d\u1293 \u130d\u121d\u1308\u121b \u12a0\u12ed\u12f0\u1208\u121d\u1362"
        )
        return {
            "prioritySuggestion": "urgent",
            "priorityReason": reason,
        }

    reason = (
        "No emergency or urgent routing rule matched this message. "
        "Routine review is only a queue suggestion; it does not mean "
        "the concern is safe or does not need clinical assessment."
        if selected_language == "en"
        else "\u1260\u12da\u1205 \u1218\u120d\u12d5\u12ad\u1275 \u120b\u12ed \u12e8\u12a0\u1235\u1278\u12b3\u12ed \u12c8\u12ed\u121d \u1348\u1323\u1295 \u121b\u1235\u1270\u120b\u1208\u134a\u12eb \u1215\u130d \u12a0\u120d\u1270\u12db\u1218\u12f0\u121d\u1362 \u1218\u12f0\u1260\u129b \u130d\u121d\u1308\u121b \u12e8\u12c8\u1228\u134b \u121b\u1235\u1270\u12ab\u12a8\u12eb \u1325\u1246\u121b \u1265\u127b \u1290\u12cd\u1364 \u127d\u130d\u1229 \u12f0\u1205\u1293 \u1290\u12cd \u12c8\u12ed\u121d \u12e8\u1215\u12ad\u121d\u1293 \u130d\u121d\u1308\u121b \u12a0\u12eb\u1235\u1348\u120d\u1308\u12cd\u121d \u121b\u1208\u1275 \u12a0\u12ed\u12f0\u1208\u121d\u1362"
    )
    return {
        "prioritySuggestion": "routine_review",
        "priorityReason": reason,
    }


def evaluate_safety(message: str, language: str = "en") -> SafetyResult:
    """Check urgent symptoms and restricted requests, then offer advisories."""
    selected_language = "am" if language == "am" else "en"

    if _matches_urgent(message):
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

    if _matches(DIZZINESS_PATTERNS, message):
        return {
            "blocked": False,
            "urgent": False,
            "message": (
                DIZZINESS_MESSAGE_AM
                if selected_language == "am"
                else DIZZINESS_MESSAGE_EN
            ),
        }

    return {
        "blocked": False,
        "urgent": False,
        "message": None,
    }
