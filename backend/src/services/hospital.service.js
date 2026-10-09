import { labResults, medicalHistory, medications, patients, } from "../data/patients";
export class HospitalService {
    getPatientProfile(patientId) {
        return patients.find((patient) => patient.id === patientId) ?? null;
    }
    getLatestLabResults(patientId) {
        const results = labResults[patientId] ?? [];
        if (results.length === 0) {
            return [];
        }
        const latestDate = results.reduce((latest, current) => current.date > latest ? current.date : latest, results[0].date);
        return results.filter((result) => result.date === latestDate);
    }
    getAllLabResults(patientId) {
        return labResults[patientId] ?? [];
    }
    getMedications(patientId) {
        return medications[patientId] ?? [];
    }
    getMedicalHistory(patientId) {
        return medicalHistory[patientId] ?? [];
    }
}
export const hospitalService = new HospitalService();
//# sourceMappingURL=hospital.service.js.map