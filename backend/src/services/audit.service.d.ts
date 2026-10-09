interface AuditEntry {
    timestamp: string;
    patientId: string;
    conversationId: string;
    event: string;
    details?: unknown;
}
export declare function recordAuditEvent(entry: Omit<AuditEntry, "timestamp">): void;
export declare function getAuditLog(): AuditEntry[];
export {};
//# sourceMappingURL=audit.service.d.ts.map