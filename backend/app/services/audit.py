"""Privacy-conscious, in-memory audit logging for the demo."""

from collections import deque
from copy import deepcopy
from datetime import UTC, datetime
from threading import Lock
from typing import Any, TypedDict


class AuditEntry(TypedDict, total=False):
    timestamp: str
    patientId: str
    conversationId: str
    event: str
    details: dict[str, Any]


_MAX_AUDIT_EVENTS = 1000
_audit_log: deque[AuditEntry] = deque(maxlen=_MAX_AUDIT_EVENTS)
_audit_lock = Lock()

# Only retain detail fields intended for operational auditing.
# Appointment dates, times, doctor IDs, free-text errors, request contents,
# and other unapproved fields are deliberately excluded.
_SAFE_DETAIL_STRINGS = {
    "detail",
    "language",
    "scope",
    "status",
    "dataSource",
}


def _safe_identifier(value: Any) -> str | None:
    """Accept bounded string identifiers only."""
    if not isinstance(value, str):
        return None

    value = value.strip()
    if not value:
        return None

    return value[:128]


def _sanitize_details(value: Any) -> dict[str, Any]:
    """Allowlist low-risk metadata and discard arbitrary detail fields."""
    if not isinstance(value, dict):
        return {}

    safe: dict[str, Any] = {}

    for key in _SAFE_DETAIL_STRINGS:
        item = value.get(key)
        if isinstance(item, str):
            safe[key] = item[:80]

    urgent = value.get("urgent")
    if isinstance(urgent, bool):
        safe["urgent"] = urgent

    tools_used = value.get("toolsUsed")
    if isinstance(tools_used, list):
        safe_tools = [
            tool[:80]
            for tool in tools_used[:20]
            if isinstance(tool, str)
        ]
        safe["toolsUsed"] = safe_tools

    return safe


def record_audit_event(entry: dict[str, Any]) -> None:
    """Record sanitized metadata without printing patient-linked events."""
    if not isinstance(entry, dict):
        return

    event = _safe_identifier(entry.get("event"))
    if event is None:
        return

    audit_entry: AuditEntry = {
        "timestamp": datetime.now(UTC).isoformat(),
        "event": event,
        "details": _sanitize_details(entry.get("details")),
    }

    patient_id = _safe_identifier(entry.get("patientId"))
    conversation_id = _safe_identifier(entry.get("conversationId"))

    if patient_id is not None:
        audit_entry["patientId"] = patient_id

    if conversation_id is not None:
        audit_entry["conversationId"] = conversation_id

    # Lock protects shared state when requests are handled concurrently.
    with _audit_lock:
        _audit_log.append(audit_entry)


def get_audit_log() -> list[AuditEntry]:
    """Return a defensive copy so callers cannot mutate stored events."""
    with _audit_lock:
        return deepcopy(list(_audit_log))


def reset_audit_log() -> None:
    """Clear in-memory audit events, primarily for automated tests."""
    with _audit_lock:
        _audit_log.clear()
