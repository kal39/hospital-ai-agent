from pathlib import Path

agent_path = Path("app/services/agent.py")
source = agent_path.read_text(encoding="utf-8")

def replace_once(text, old, new, description):
    count = text.count(old)
    if count != 1:
        raise RuntimeError(
            f"{description}: expected exactly one match, found {count}. "
            "No further edits were made."
        )
    return text.replace(old, new, 1)

# 1. Import the request-service exceptions.
source = replace_once(
    source,
    "from app.services.appointment_requests import get_appointment_request_service\n",
    """from app.services.appointment_requests import (
    AppointmentRequestConflict,
    AppointmentRequestNotFound,
    get_appointment_request_service,
)
""",
    "request-service import",
)

# 2. Add isolated cancellation state.
source = replace_once(
    source,
    "_completed_appointment_requests: dict[str, dict[str, Any]] = {}\n",
    """_completed_appointment_requests: dict[str, dict[str, Any]] = {}
_pending_appointment_cancellations: dict[str, dict[str, Any]] = {}
""",
    "cancellation state",
)

# 3. Add intent detectors.
helpers = r'''

def _is_appointment_request_status_query(message: str) -> bool:
    """Identify patient requests to inspect appointment-request status."""
    text = re.sub(r"\s+", " ", message.casefold()).strip()

    patterns = (
        r"\b(?:status|progress|update)\b.{0,80}\b"
        r"(?:appointment request|appointment requests|request|requests)\b",
        r"\b(?:appointment request|appointment requests|my requests)\b"
        r".{0,80}\b(?:status|progress|update|show|list|check)\b",
        r"\b(?:show|list|check)\b.{0,60}\b"
        r"(?:my appointment requests|my requests)\b",
        r"\bwhere\b.{0,50}\bmy appointment request\b",
    )
    return any(re.search(pattern, text, flags=re.DOTALL) for pattern in patterns)


def _is_appointment_request_cancellation(message: str) -> bool:
    """Match cancellation of a request, not cancellation of a confirmed visit."""
    text = re.sub(r"\s+", " ", message.casefold()).strip()

    patterns = (
        r"\b(?:cancel|withdraw|remove)\b.{0,80}\b"
        r"(?:my\s+)?(?:appointment\s+)?requests?\b",
        r"\b(?:my\s+)?(?:appointment\s+)?requests?\b.{0,80}\b"
        r"(?:cancel|withdraw|remove)\b",
        r"\bcancel\s+(?:the\s+)?request\b",
    )
    return any(re.search(pattern, text, flags=re.DOTALL) for pattern in patterns)


def _extract_appointment_request_id(message: str) -> str | None:
    """Extract only a syntactically valid synthetic request reference."""
    match = re.search(r"\bdemo-req-[a-f0-9]{12}\b", message, flags=re.IGNORECASE)
    return match.group(0).lower() if match else None
'''

source = replace_once(
    source,
    "\ndef _appointment_action_unavailable_message(language: str) -> str:\n",
    helpers + "\n\ndef _appointment_action_unavailable_message(language: str) -> str:\n",
    "appointment-request intent helpers",
)

# 4. Insert deterministic status and cancellation handling after safety checks.
handler = r'''
        # Patient request management is handled directly by the trusted
        # request service. The authenticated patient identity is always used.
        request_service = None

        if _is_appointment_request_status_query(message):
            _pending_appointment_cancellations.pop(key, None)
            _pending_appointment_requests.pop(key, None)
            _pending_appointment_selections.pop(key, None)

            request_service = get_appointment_request_service(demo_scheduler)
            request_id = _extract_appointment_request_id(message)

            try:
                if request_id:
                    requests = [
                        request_service.get_patient_request(
                            patient_id=patient_id,
                            request_id=request_id,
                        )
                    ]
                else:
                    requests = request_service.list_patient_requests(patient_id)
            except AppointmentRequestNotFound:
                requests = []

            if not requests:
                response_message = (
                    "I couldn't find an appointment request matching that "
                    "reference in your account. Please check the reference "
                    "or ask me to show your appointment requests."
                )
            else:
                lines = [
                    "Your appointment request status (synthetic demonstration data):"
                ]
                for item in requests:
                    lines.extend([
                        "",
                        f"Reference: {item.get('requestId', 'Unavailable')}",
                        f"Status: {str(item.get('status', 'unknown')).replace('_', ' ').title()}",
                        f"Department: {item.get('department') or 'Not specified'}",
                        f"Preferred doctor: {item.get('preferredDoctor') or 'Not specified'}",
                        f"Preferred date: {item.get('preferredDateStart') or 'Not specified'}",
                    ])

                lines.extend([
                    "",
                    "A submitted request is not a confirmed appointment. "
                    "Hospital staff must review it and confirm an appointment separately.",
                    "These records are from the local synthetic demonstration, "
                    "not the live hospital system.",
                ])
                response_message = "\n".join(lines)

            _store_turn(key, message, response_message)
            try:
                record_audit_event({
                    "patientId": patient_id,
                    "conversationId": conversation_id,
                    "event": "PATIENT_APPOINTMENT_REQUEST_STATUS_VIEWED",
                    "details": {
                        "requestCount": len(requests),
                        "dataSource": "synthetic_demo",
                    },
                })
            except Exception:
                pass

            return {
                "message": response_message,
                "toolsUsed": [],
                "safetyFlag": False,
            }

        pending_cancellation = _pending_appointment_cancellations.get(key)

        if pending_cancellation is not None:
            cancellation_status = pending_cancellation.get("status")

            if cancellation_status == "awaiting_selection":
                selection = re.fullmatch(r"\s*(\d+)\s*", message)
                selected_request = None

                if selection:
                    index = int(selection.group(1)) - 1
                    choices = pending_cancellation.get("requests", [])
                    if 0 <= index < len(choices):
                        selected_request = choices[index]
                else:
                    supplied_id = _extract_appointment_request_id(message)
                    if supplied_id:
                        selected_request = next(
                            (
                                item for item in pending_cancellation.get(
                                    "requests", []
                                )
                                if item.get("requestId") == supplied_id
                            ),
                            None,
                        )

                if _consent_decision(message) == "no":
                    _pending_appointment_cancellations.pop(key, None)
                    response_message = (
                        "Okay. I stopped the cancellation process. "
                        "Your appointment request has not been changed."
                    )
                elif selected_request is None:
                    response_message = (
                        "Please select one of the listed request numbers or "
                        "provide its exact reference. Reply NO to stop. "
                        "Nothing has been cancelled."
                    )
                else:
                    try:
                        # Re-fetch using the authenticated patient identity.
                        verified_request = (
                            get_appointment_request_service(
                                demo_scheduler
                            ).get_patient_request(
                                patient_id=patient_id,
                                request_id=selected_request["requestId"],
                            )
                        )
                    except AppointmentRequestNotFound:
                        _pending_appointment_cancellations.pop(key, None)
                        response_message = (
                            "I couldn't verify that request in your account. "
                            "No cancellation was made."
                        )
                    else:
                        _pending_appointment_cancellations[key] = {
                            "status": "awaiting_confirmation",
                            "request_id": verified_request["requestId"],
                        }
                        response_message = (
                            "Please confirm that you want to cancel this "
                            "appointment request:\n"
                            f"Reference: {verified_request['requestId']}\n"
                            f"Department: {verified_request.get('department') or 'Not specified'}\n"
                            f"Preferred doctor: {verified_request.get('preferredDoctor') or 'Not specified'}\n"
                            f"Preferred date: {verified_request.get('preferredDateStart') or 'Not specified'}\n"
                            f"Current status: {verified_request.get('status', 'unknown')}\n\n"
                            "Reply YES to cancel this request, or NO to keep it. "
                            "This does not cancel a confirmed appointment. "
                            "No change has been made yet."
                        )

                _store_turn(key, message, response_message)
                return {
                    "message": response_message,
                    "toolsUsed": [],
                    "safetyFlag": False,
                }

            if cancellation_status == "awaiting_confirmation":
                decision = _consent_decision(message)

                if decision == "no":
                    _pending_appointment_cancellations.pop(key, None)
                    response_message = (
                        "Okay. Your appointment request has not been cancelled."
                    )
                elif decision != "yes":
                    response_message = (
                        "Please reply YES to cancel the displayed appointment "
                        "request, or NO to keep it. No change has been made."
                    )
                else:
                    request_id = pending_cancellation.get("request_id")
                    try:
                        cancelled_request = (
                            get_appointment_request_service(
                                demo_scheduler
                            ).cancel_patient_request(
                                patient_id=patient_id,
                                request_id=request_id,
                            )
                        )
                    except AppointmentRequestNotFound:
                        response_message = (
                            "I couldn't verify that request in your account. "
                            "No cancellation was made."
                        )
                        _pending_appointment_cancellations.pop(key, None)
                    except AppointmentRequestConflict:
                        response_message = (
                            "That request is no longer eligible for cancellation. "
                            "It may already have been processed. Please check its "
                            "current status or contact the hospital."
                        )
                        _pending_appointment_cancellations.pop(key, None)
                    except Exception:
                        response_message = (
                            "I couldn't verify whether the cancellation completed "
                            "because of a temporary system problem. Please check "
                            "the request status before trying again."
                        )
                        _pending_appointment_cancellations.pop(key, None)
                    else:
                        _pending_appointment_cancellations.pop(key, None)
                        response_message = (
                            "APPOINTMENT REQUEST CANCELLED - synthetic demo only.\n"
                            f"Reference: {cancelled_request['requestId']}\n"
                            f"Status: {cancelled_request['status']}\n\n"
                            "This cancellation applies to the appointment request, "
                            "not to a confirmed appointment. The local synthetic "
                            "demonstration is not connected to the live hospital system."
                        )

                _store_turn(key, message, response_message)
                try:
                    record_audit_event({
                        "patientId": patient_id,
                        "conversationId": conversation_id,
                        "event": "PATIENT_APPOINTMENT_REQUEST_CANCELLATION_HANDLED",
                        "details": {},
                    })
                except Exception:
                    pass
                return {
                    "message": response_message,
                    "toolsUsed": [],
                    "safetyFlag": False,
                }

        if _is_appointment_request_cancellation(message):
            # A new request-cancellation task interrupts any unfinished
            # appointment discovery or selection in this conversation.
            _pending_appointment_requests.pop(key, None)
            _pending_appointment_selections.pop(key, None)

            request_service = get_appointment_request_service(demo_scheduler)
            try:
                patient_requests = request_service.list_patient_requests(
                    patient_id
                )
            except Exception:
                patient_requests = []

            eligible_requests = [
                item for item in patient_requests
                if item.get("status") in {
                    "submitted",
                    "under_review",
                    "needs_information",
                    "appointment_offered",
                }
            ]

            supplied_id = _extract_appointment_request_id(message)
            if supplied_id:
                eligible_requests = [
                    item for item in eligible_requests
                    if item.get("requestId") == supplied_id
                ]

            if not eligible_requests:
                response_message = (
                    "I couldn't find an eligible appointment request to cancel "
                    "in your account. Confirmed appointments, completed requests, "
                    "and already cancelled requests cannot be cancelled through "
                    "this request workflow."
                )
            else:
                _pending_appointment_cancellations[key] = {
                    "status": "awaiting_selection",
                    "requests": eligible_requests,
                }
                lines = [
                    "These are your eligible appointment requests "
                    "(synthetic demonstration data):"
                ]
                for index, item in enumerate(eligible_requests, start=1):
                    lines.append(
                        f"{index}. {item.get('requestId')} - "
                        f"{item.get('department') or 'Department not specified'} - "
                        f"{item.get('preferredDoctor') or 'Doctor not specified'} - "
                        f"{item.get('preferredDateStart') or 'Date not specified'} - "
                        f"Status: {item.get('status', 'unknown')}"
                    )
                lines.extend([
                    "",
                    "Reply with the number or exact reference of the request "
                    "you want to cancel. I will show its details and ask for "
                    "separate confirmation before making any change.",
                    "This is synthetic local demonstration data.",
                ])
                response_message = "\n".join(lines)

            _store_turn(key, message, response_message)
            try:
                record_audit_event({
                    "patientId": patient_id,
                    "conversationId": conversation_id,
                    "event": "PATIENT_APPOINTMENT_REQUEST_CANCELLATION_STARTED",
                    "details": {
                        "eligibleRequestCount": len(eligible_requests),
                        "dataSource": "synthetic_demo",
                    },
                })
            except Exception:
                pass

            return {
                "message": response_message,
                "toolsUsed": [],
                "safetyFlag": False,
            }

'''

source = replace_once(
    source,
    "        pending_selection = _pending_appointment_selections.get(key)\n",
    handler + "        pending_selection = _pending_appointment_selections.get(key)\n",
    "request-management handler insertion",
)

agent_path.write_text(source, encoding="utf-8")

# 5. Reset the new state in all existing agent test fixtures.
fixture_paths = [
    Path("tests/test_agent_consent.py"),
    Path("tests/test_agent_safety_integration.py"),
    Path("tests/test_agent_upcoming_appointments.py"),
    Path("tests/test_conversation_isolation.py"),
]

for path in fixture_paths:
    content = path.read_text(encoding="utf-8")
    anchor = "    agent_module._completed_appointment_requests.clear()\n"
    count = content.count(anchor)
    if count != 2:
        raise RuntimeError(
            f"{path}: expected two fixture cleanup anchors, found {count}"
        )
    content = content.replace(
        anchor,
        anchor + "    agent_module._pending_appointment_cancellations.clear()\n",
    )
    path.write_text(content, encoding="utf-8")

print("Patch applied.")
print("Updated agent.py and four test fixtures.")
