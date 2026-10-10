
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

  it("returns the second synthetic patient's profile", () => {
    const profile = executeHospitalTool(
      "getPatientProfile",
      "patient-002"
    ) as { id: string };

    expect(profile.id).toBe("patient-002");
  });

  it("does not return a profile for an unknown patient", () => {
    expect(() =>
      executeHospitalTool("getPatientProfile", "patient-999")
    ).toThrow("Patient record not found.");
  });

  it("keeps lab results separated between patients", () => {
    const patientOneLabs = executeHospitalTool(
      "getLatestLabResults",
      "patient-001"
    ) as Array<{ id: string }>;

    const patientTwoLabs = executeHospitalTool(
      "getLatestLabResults",
      "patient-002"
    ) as Array<{ id: string }>;

    expect(patientOneLabs.length).toBeGreaterThan(0);
    expect(patientTwoLabs.length).toBeGreaterThan(0);

    expect(patientOneLabs.map((lab) => lab.id))
      .not.toContain("lab-004");

    expect(patientTwoLabs.map((lab) => lab.id))
      .not.toContain("lab-001");

    expect(patientOneLabs.map((lab) => lab.id))
      .not.toEqual(patientTwoLabs.map((lab) => lab.id));
  });

  it("keeps medications separated between patients", () => {
    const patientOneMeds = executeHospitalTool(
      "getMedications",
      "patient-001"
    ) as Array<{ id: string }>;

    const patientTwoMeds = executeHospitalTool(
      "getMedications",
      "patient-002"
    ) as Array<{ id: string }>;

    expect(patientOneMeds.map((med) => med.id))
      .toEqual(["med-001"]);

    expect(patientTwoMeds.map((med) => med.id))
      .toEqual(["med-002"]);

    expect(patientOneMeds).not.toEqual(patientTwoMeds);
  });

  it("keeps medical history separated between patients", () => {
    const patientOneHistory = executeHospitalTool(
      "getMedicalHistory",
      "patient-001"
    ) as Array<{ id: string }>;

    const patientTwoHistory = executeHospitalTool(
      "getMedicalHistory",
      "patient-002"
    ) as Array<{ id: string }>;

    expect(patientOneHistory.map((item) => item.id))
      .not.toContain("history-004");

    expect(patientTwoHistory.map((item) => item.id))
      .not.toContain("history-001");

    expect(patientOneHistory.map((item) => item.id))
      .not.toEqual(patientTwoHistory.map((item) => item.id));
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
