import { hospitalService } from "../services/hospital.service";

export function getPatientProfile(patientId: string) {
  const patient = hospitalService.getPatientProfile(patientId);

  if (!patient) {
    throw new Error("Patient record not found.");
  }

  return patient;
}