
import { describe, expect, it } from "vitest";
import { hospitalService } from "./hospital.service.js";

describe("HospitalService", () => {
  it("returns the profile for a known synthetic patient", () => {
    const profile = hospitalService.getPatientProfile("patient-001");

    expect(profile).not.toBeNull();
    expect(profile?.id).toBe("patient-001");
  });

  it("returns null for an unknown patient profile", () => {
    expect(
      hospitalService.getPatientProfile("patient-999")
    ).toBeNull();
  });

  it("returns no records for an unknown patient", () => {
    expect(
      hospitalService.getAllLabResults("patient-999")
    ).toEqual([]);

    expect(
      hospitalService.getMedications("patient-999")
    ).toEqual([]);

    expect(
      hospitalService.getMedicalHistory("patient-999")
    ).toEqual([]);
  });

  it("returns distinct profiles for different patients", () => {
    const patientOne =
      hospitalService.getPatientProfile("patient-001");

    const patientTwo =
      hospitalService.getPatientProfile("patient-002");

    expect(patientOne?.id).toBe("patient-001");
    expect(patientTwo?.id).toBe("patient-002");
    expect(patientOne).not.toEqual(patientTwo);
  });

  it("keeps lab results separated between patients", () => {
    const patientOneLabs =
      hospitalService.getAllLabResults("patient-001");

    const patientTwoLabs =
      hospitalService.getAllLabResults("patient-002");

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
    const patientOneMeds =
      hospitalService.getMedications("patient-001");

    const patientTwoMeds =
      hospitalService.getMedications("patient-002");

    expect(patientOneMeds.map((med) => med.id))
      .toEqual(["med-001"]);

    expect(patientTwoMeds.map((med) => med.id))
      .toEqual(["med-002"]);

    expect(patientOneMeds).not.toEqual(patientTwoMeds);
  });

  it("keeps medical history separated between patients", () => {
    const patientOneHistory =
      hospitalService.getMedicalHistory("patient-001");

    const patientTwoHistory =
      hospitalService.getMedicalHistory("patient-002");

    expect(patientOneHistory.map((item) => item.id))
      .not.toContain("history-004");

    expect(patientTwoHistory.map((item) => item.id))
      .not.toContain("history-001");

    expect(patientOneHistory.map((item) => item.id))
      .not.toEqual(patientTwoHistory.map((item) => item.id));
  });
});
