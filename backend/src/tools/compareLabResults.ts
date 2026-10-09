import { hospitalService } from "../services/hospital.service.js";

export function compareLabResults(patientId: string) {
  const results = hospitalService.getAllLabResults(patientId);

  const grouped = new Map<string, typeof results>();

  for (const result of results) {
    const existing = grouped.get(result.testName) ?? [];
    existing.push(result);
    grouped.set(result.testName, existing);
  }

  return Array.from(grouped.entries()).map(
    ([testName, measurements]) => {
      const sorted = [...measurements].sort((a, b) =>
        a.date.localeCompare(b.date)
      );

      const previous = sorted.at(-2);
      const latest = sorted.at(-1);

      return {
        testName,
        previous,
        latest,
        change:
          previous && latest
            ? Number((latest.value - previous.value).toFixed(2))
            : null,
      };
    }
  );
}