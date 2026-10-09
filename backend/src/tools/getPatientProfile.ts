import { hospitalService } from "../services/hospital.service.js";

export function getPatientProfile(patientId: string) {
  const patient = hospitalService.getPatientProfile(patientId);

  if (!patient) {
    throw new Error("Patient record not found.");
  }

  return patient;
}