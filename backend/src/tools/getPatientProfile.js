import { hospitalService } from "../services/hospital.service";
export function getPatientProfile(patientId) {
    const patient = hospitalService.getPatientProfile(patientId);
    if (!patient) {
        throw new Error("Patient record not found.");
    }
    return patient;
}
//# sourceMappingURL=getPatientProfile.js.map