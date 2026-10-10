
import { getPatientProfile } from "../tools/getPatientProfile.js";
import { getLatestLabResults } from "../tools/getLatestLabResults.js";
import { getMedications } from "../tools/getMedications.js";
import { getMedicalHistory } from "../tools/getMedicalHistory.js";
import { compareLabResults } from "../tools/compareLabResults.js";

/**
 * Executes only explicitly approved hospital tools.
 *
 * The patient ID must come from trusted backend authentication
 * context, never from Gemini's function arguments or user input.
 */
export function executeHospitalTool(
  toolName: string,
  patientId: string
): unknown {
  if (!patientId || !patientId.trim()) {
    throw new Error("Authenticated patient identity is required.");
  }

  switch (toolName) {
    case "getLatestLabResults":
      return getLatestLabResults(patientId);

    case "compareLabResults":
      return compareLabResults(patientId);

    case "getMedications":
      return getMedications(patientId);

    case "getMedicalHistory":
      return getMedicalHistory(patientId);

    case "getPatientProfile":
      return getPatientProfile(patientId);

    default:
      throw new Error(
        `Unauthorized or unknown hospital tool: ${toolName}`
      );
  }
}
