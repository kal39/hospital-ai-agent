export type Language = "en" | "am";
export interface Patient {
    id: string;
    firstName: string;
    lastName: string;
    dateOfBirth: string;
    bloodType: string;
    allergies: string[];
    diagnoses: string[];
}
export interface LabResult {
    id: string;
    testName: string;
    value: number;
    unit: string;
    referenceRange: string;
    status: "normal" | "high" | "low";
    date: string;
}
export interface Medication {
    id: string;
    name: string;
    dosage: string;
    frequency: string;
    instructions: string;
    active: boolean;
}
export interface MedicalHistoryItem {
    id: string;
    date: string;
    type: "diagnosis" | "procedure" | "visit" | "treatment";
    title: string;
    description: string;
}
//# sourceMappingURL=patient.d.ts.map