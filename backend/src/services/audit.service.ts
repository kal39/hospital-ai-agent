interface AuditEntry {
  timestamp: string;
  patientId: string;
  conversationId: string;
  event: string;
  details?: unknown;
}

const auditLog: AuditEntry[] = [];

export function recordAuditEvent(
  entry: Omit<AuditEntry, "timestamp">
) {
  auditLog.push({
    timestamp: new Date().toISOString(),
    ...entry,
  });

  console.log("[AUDIT]", auditLog.at(-1));
}

export function getAuditLog() {
  return [...auditLog];
}