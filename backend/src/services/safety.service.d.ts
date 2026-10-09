export interface SafetyResult {
    blocked: boolean;
    urgent: boolean;
    message?: string;
}
export declare function evaluateSafety(input: string): SafetyResult;
//# sourceMappingURL=safety.service.d.ts.map