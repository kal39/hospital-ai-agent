export const medicalGlossary = [
    {
        english: "Hemoglobin",
        amharic: "ሄሞግሎቢን",
        explanation: "A protein in red blood cells that carries oxygen through the body.",
    },
    {
        english: "Fasting Blood Glucose",
        amharic: "የጾም የደም ስኳር",
        explanation: "The amount of glucose in the blood after fasting.",
    },
    {
        english: "Creatinine",
        amharic: "ክሬቲኒን",
        explanation: "A substance commonly measured to help assess kidney function.",
    },
    {
        english: "Blood Pressure",
        amharic: "የደም ግፊት",
        explanation: "The force of blood against the walls of blood vessels.",
    },
    {
        english: "Hypertension",
        amharic: "የደም ግፊት መጨመር",
        explanation: "Persistently elevated blood pressure.",
    },
];
export function getGlossaryContext() {
    return medicalGlossary
        .map((term) => `${term.english} = ${term.amharic}. ${term.explanation}`)
        .join("\n");
}
//# sourceMappingURL=medicalTerms.js.map