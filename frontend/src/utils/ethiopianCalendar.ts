export type EthiopianDate = {
  year: number;
  month: number;
  day: number;
};

export const ETHIOPIAN_MONTHS_EN = [
  "Meskerem",
  "Tikimt",
  "Hidar",
  "Tahsas",
  "Tir",
  "Yekatit",
  "Megabit",
  "Miyazya",
  "Ginbot",
  "Sene",
  "Hamle",
  "Nehase",
  "Pagume",
] as const;

export const ETHIOPIAN_MONTHS_AM = [
  "መስከረም",
  "ጥቅምት",
  "ሕዳር",
  "ታኅሣሥ",
  "ጥር",
  "የካቲት",
  "መጋቢት",
  "ሚያዝያ",
  "ግንቦት",
  "ሰኔ",
  "ሐምሌ",
  "ነሐሴ",
  "ጳጉሜ",
] as const;

const ethiopianFormatter = new Intl.DateTimeFormat(
  "en-u-ca-ethiopic-nu-latn",
  {
    calendar: "ethiopic",
    numberingSystem: "latn",
    year: "numeric",
    month: "numeric",
    day: "numeric",
    timeZone: "UTC",
  },
);

function isoToUtcDate(isoDate: string): Date {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(isoDate)) {
    throw new Error(`Invalid Gregorian ISO date: ${isoDate}`);
  }

  const [year, month, day] = isoDate.split("-").map(Number);
  const date = new Date(Date.UTC(year, month - 1, day));

  if (
    date.getUTCFullYear() !== year ||
    date.getUTCMonth() !== month - 1 ||
    date.getUTCDate() !== day
  ) {
    throw new Error(`Invalid Gregorian calendar date: ${isoDate}`);
  }

  return date;
}

function readEthiopianDate(date: Date): EthiopianDate {
  const parts = ethiopianFormatter.formatToParts(date);
  const values = Object.fromEntries(
    parts
      .filter((part) => part.type !== "literal")
      .map((part) => [part.type, Number(part.value)]),
  );

  const year = values.year;
  const month = values.month;
  const day = values.day;

  if (
    !Number.isInteger(year) ||
    !Number.isInteger(month) ||
    !Number.isInteger(day) ||
    month < 1 ||
    month > 13 ||
    day < 1 ||
    day > 30
  ) {
    throw new Error("The runtime returned an invalid Ethiopian date.");
  }

  return { year, month, day };
}

export function gregorianToEthiopian(isoDate: string): EthiopianDate {
  return readEthiopianDate(isoToUtcDate(isoDate));
}

export function formatEthiopianDate(
  isoDate: string,
  language: "en" | "am" = "en",
): string {
  const { year, month, day } = gregorianToEthiopian(isoDate);
  const monthName =
    language === "am"
      ? ETHIOPIAN_MONTHS_AM[month - 1]
      : ETHIOPIAN_MONTHS_EN[month - 1];

  return language === "am"
    ? `${monthName} ${day}, ${year} ዓ.ም.`
    : `${monthName} ${day}, ${year} E.C.`;
}

export function ethiopianToGregorian(
  ethiopianDate: EthiopianDate,
): string {
  const { year, month, day } = ethiopianDate;

  if (
    !Number.isInteger(year) ||
    !Number.isInteger(month) ||
    !Number.isInteger(day) ||
    year < 1 ||
    month < 1 ||
    month > 13 ||
    day < 1 ||
    day > 30
  ) {
    throw new Error("Invalid Ethiopian date.");
  }

  // An Ethiopian year begins in September of its approximate Gregorian year.
  // Search actual Gregorian dates using Intl rather than relying on a
  // hardcoded date table or a fixed Ethiopian New Year assumption.
  const firstSearchDate = Date.UTC(year + 7, 8, 1);
  const lastSearchDate = Date.UTC(year + 8, 9, 15);
  const oneDay = 24 * 60 * 60 * 1000;

  for (
    let timestamp = firstSearchDate;
    timestamp <= lastSearchDate;
    timestamp += oneDay
  ) {
    const candidate = new Date(timestamp);
    const converted = readEthiopianDate(candidate);

    if (
      converted.year === year &&
      converted.month === month &&
      converted.day === day
    ) {
      const gregorianYear = candidate.getUTCFullYear();
      const gregorianMonth = String(candidate.getUTCMonth() + 1).padStart(
        2,
        "0",
      );
      const gregorianDay = String(candidate.getUTCDate()).padStart(2, "0");

      return `${gregorianYear}-${gregorianMonth}-${gregorianDay}`;
    }
  }

  throw new Error(
    `Ethiopian date does not exist: ${year}-${month}-${day}`,
  );
}

export function daysInEthiopianMonth(
  year: number,
  month: number,
): number {
  if (
    !Number.isInteger(year) ||
    year < 1 ||
    !Number.isInteger(month) ||
    month < 1 ||
    month > 13
  ) {
    throw new Error("Invalid Ethiopian year or month.");
  }

  if (month !== 13) return 30;

  // Pagume has five or six days, determined by the calendar itself.
  const nextYearMeskerem = ethiopianToGregorian({
    year: year + 1,
    month: 1,
    day: 1,
  });
  const currentYearMeskerem = ethiopianToGregorian({
    year,
    month: 1,
    day: 1,
  });

  const difference =
    (isoToUtcDate(nextYearMeskerem).getTime() -
      isoToUtcDate(currentYearMeskerem).getTime()) /
    (24 * 60 * 60 * 1000);

  return difference === 366 ? 6 : 5;
}
