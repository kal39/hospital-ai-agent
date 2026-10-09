import { hospitalService } from "../services/hospital.service.js";

export function getMedications(patientId: string) {
  return hospitalService.getMedications(patientId);
}