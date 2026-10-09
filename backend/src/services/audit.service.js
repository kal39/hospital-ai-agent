const auditLog = [];
export function recordAuditEvent(entry) {
    auditLog.push({
        timestamp: new Date().toISOString(),
        ...entry,
    });
    console.log("[AUDIT]", auditLog.at(-1));
}
export function getAuditLog() {
    return [...auditLog];
}
//# sourceMappingURL=audit.service.js.map