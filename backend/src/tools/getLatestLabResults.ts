import { hospitalService } from "../services/hospital.service";

export function getLatestLabResults(patientId: string) {
  return hospitalService.getLatestLabResults(patientId);
}