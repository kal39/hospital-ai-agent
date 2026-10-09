import {
  labResults,
  medicalHistory,
  medications,
  patients,
} from "../data/patients.js";

export class HospitalService {
  getPatientProfile(patientId: string) {
    return patients.find((patient) => patient.id === patientId) ?? null;
  }

  getLatestLabResults(patientId: string) {
    const results = labResults[patientId] ?? [];

    if (results.length === 0) {
      return [];
    }

    const latestDate = results.reduce((latest, current) =>
      current.date > latest ? current.date : latest
    , results[0].date);

    return results.filter((result) => result.date === latestDate);
  }

  getAllLabResults(patientId: string) {
    return labResults[patientId] ?? [];
  }

  getMedications(patientId: string) {
    return medications[patientId] ?? [];
  }

  getMedicalHistory(patientId: string) {
    return medicalHistory[patientId] ?? [];
  }
}

export const hospitalService = new HospitalService();