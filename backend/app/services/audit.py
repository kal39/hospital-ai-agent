
"""In-memory audit logging for agent activity."""

from datetime import UTC, datetime
from typing import Any, TypedDict


class AuditEntry(TypedDict, total=False):
    timestamp: str
    patientId: str
    conversationId: str
    event: str
    details: Any


_audit_log: list[AuditEntry] = []


def record_audit_event(
    entry: dict[str, Any],
) -> None:
    """Record an audit event with its UTC timestamp."""
    audit_entry: AuditEntry = {
        "timestamp": datetime.now(UTC).isoformat(),
        **entry,
    }

    _audit_log.append(audit_entry)
    print("[AUDIT]", audit_entry)


def get_audit_log() -> list[AuditEntry]:
    """Return a copy of the audit log."""
    return list(_audit_log)
