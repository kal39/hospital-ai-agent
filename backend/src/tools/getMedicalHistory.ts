import { hospitalService } from "../services/hospital.service.js";

export function getMedicalHistory(patientId: string) {
  return hospitalService.getMedicalHistory(patientId);
}