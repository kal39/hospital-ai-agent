import { hospitalService } from "../services/hospital.service.js";

export function getLatestLabResults(patientId: string) {
  return hospitalService.getLatestLabResults(patientId);
}