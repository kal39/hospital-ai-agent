
import { describe, expect, it } from "vitest";
import { executeHospitalTool } from "./toolExecutor.js";

describe("Hospital tool execution boundary", () => {
  it("rejects unknown tool names", () => {
    expect(() =>
      executeHospitalTool("deletePatientRecords", "patient-001")
    ).toThrow("Unauthorized or unknown hospital tool");
  });

  it("rejects a missing patient ID", () => {
    expect(() =>
      executeHospitalTool("getMedications", "")
    ).toThrow("Authenticated patient identity is required.");
  });

  it("returns the requested synthetic patient's profile", () => {
    const profile = executeHospitalTool(
      "getPatientProfile",
      "patient-001"
    ) as { id: string };

    expect(profile.id).toBe("patient-001");
  });

  it("does not return a profile for an unknown patient", () => {
    expect(() =>
      executeHospitalTool("getPatientProfile", "patient-999")
    ).toThrow("Patient record not found.");
  });

  it("returns no lab results for an unknown patient", () => {
    expect(
      executeHospitalTool("getLatestLabResults", "patient-999")
    ).toEqual([]);
  });

  it("returns no medications for an unknown patient", () => {
    expect(
      executeHospitalTool("getMedications", "patient-999")
    ).toEqual([]);
  });

  it("returns no medical history for an unknown patient", () => {
    expect(
      executeHospitalTool("getMedicalHistory", "patient-999")
    ).toEqual([]);
  });
});
