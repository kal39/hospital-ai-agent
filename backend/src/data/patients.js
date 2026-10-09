import { LabResult, Medication, MedicalHistoryItem, Patient, } from "../types/patient";
export const patients = [
    {
        id: "patient-001",
        firstName: "Abebe",
        lastName: "Kebede",
        dateOfBirth: "1998-04-15",
        bloodType: "O+",
        allergies: ["Penicillin"],
        diagnoses: ["Hypertension"],
    },
];
export const labResults = {
    "patient-001": [
        {
            id: "lab-001",
            testName: "Hemoglobin",
            value: 13.8,
            unit: "g/dL",
            referenceRange: "13.0-17.0",
            status: "normal",
            date: "2026-10-01",
        },
        {
            id: "lab-002",
            testName: "Fasting Blood Glucose",
            value: 112,
            unit: "mg/dL",
            referenceRange: "70-99",
            status: "high",
            date: "2026-10-01",
        },
        {
            id: "lab-003",
            testName: "Creatinine",
            value: 0.9,
            unit: "mg/dL",
            referenceRange: "0.7-1.3",
            status: "normal",
            date: "2026-10-01",
        },
    ],
};
export const medications = {
    "patient-001": [
        {
            id: "med-001",
            name: "Amlodipine",
            dosage: "5 mg",
            frequency: "Once daily",
            instructions: "Take in the morning with or without food.",
            active: true,
        },
    ],
};
export const medicalHistory = {
    "patient-001": [
        {
            id: "history-001",
            date: "2026-08-15",
            type: "visit",
            title: "Routine follow-up",
            description: "Routine hypertension follow-up.",
        },
        {
            id: "history-002",
            date: "2026-09-10",
            type: "treatment",
            title: "Medication review",
            description: "Amlodipine therapy reviewed.",
        },
        {
            id: "history-003",
            date: "2026-10-01",
            type: "visit",
            title: "Laboratory testing",
            description: "Routine blood laboratory tests performed.",
        },
    ],
};
//# sourceMappingURL=patients.js.map