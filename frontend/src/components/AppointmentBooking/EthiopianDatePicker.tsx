import { useMemo } from "react";
import type { Language } from "../../types/chat";
import {
  daysInEthiopianMonth,
  ethiopianToGregorian,
  gregorianToEthiopian,
  ETHIOPIAN_MONTHS_AM,
} from "../../utils/ethiopianCalendar";

interface EthiopianDatePickerProps {
  language: Language;
  value: string;
  minDate: string;
  onChange: (gregorianIsoDate: string) => void;
}

const ENGLISH_MONTHS = [
  "January",
  "February",
  "March",
  "April",
  "May",
  "June",
  "July",
  "August",
  "September",
  "October",
  "November",
  "December",
];

function getGregorianParts(isoDate: string) {
  const [year, month, day] = isoDate.split("-").map(Number);
  return { year, month, day };
}

function getGregorianMonthDays(year: number, month: number) {
  return new Date(Date.UTC(year, month, 0)).getUTCDate();
}

function toIsoDate(year: number, month: number, day: number) {
  return [
    String(year).padStart(4, "0"),
    String(month).padStart(2, "0"),
    String(day).padStart(2, "0"),
  ].join("-");
}

export default function EthiopianDatePicker({
  language,
  value,
  minDate,
  onChange,
}: EthiopianDatePickerProps) {
  const am = language === "am";

  const selected = useMemo(
    () => gregorianToEthiopian(value || minDate),
    [value, minDate],
  );

  const minimum = useMemo(
    () => gregorianToEthiopian(minDate),
    [minDate],
  );

  const ethiopianYears = useMemo(
    () => Array.from({ length: 4 }, (_, index) => minimum.year + index),
    [minimum.year],
  );

  const ethiopianMonthDays = daysInEthiopianMonth(
    selected.year,
    selected.month,
  );

  const gregorian = useMemo(
    () => getGregorianParts(value || minDate),
    [value, minDate],
  );

  const minimumGregorian = useMemo(
    () => getGregorianParts(minDate),
    [minDate],
  );

  const gregorianYears = useMemo(
    () =>
      Array.from(
        { length: 4 },
        (_, index) => minimumGregorian.year + index,
      ),
    [minimumGregorian.year],
  );

  const gregorianMonthDays = getGregorianMonthDays(
    gregorian.year,
    gregorian.month,
  );

  function updateEthiopianDate(year: number, month: number, day: number) {
    const safeDay = Math.min(
      day,
      daysInEthiopianMonth(year, month),
    );

    try {
      const isoDate = ethiopianToGregorian({
        year,
        month,
        day: safeDay,
      });

      if (isoDate >= minDate) {
        onChange(isoDate);
      }
    } catch {
      // Keep the last valid selection.
    }
  }

  function updateGregorianDate(year: number, month: number, day: number) {
    const safeDay = Math.min(
      day,
      getGregorianMonthDays(year, month),
    );
    const isoDate = toIsoDate(year, month, safeDay);

    if (isoDate >= minDate) {
      onChange(isoDate);
    }
  }

  if (!am) {
    return (
      <div className="ethiopian-date-picker">
        <div className="ethiopian-date-fields">
          <label>
            <span>Month</span>
            <select
              aria-label="Appointment month"
              value={gregorian.month}
              onChange={(event) =>
                updateGregorianDate(
                  gregorian.year,
                  Number(event.target.value),
                  gregorian.day,
                )
              }
              required
            >
              {ENGLISH_MONTHS.map((month, index) => (
                <option key={month} value={index + 1}>
                  {month}
                </option>
              ))}
            </select>
          </label>

          <label>
            <span>Day</span>
            <select
              aria-label="Appointment day"
              value={gregorian.day}
              onChange={(event) =>
                updateGregorianDate(
                  gregorian.year,
                  gregorian.month,
                  Number(event.target.value),
                )
              }
              required
            >
              {Array.from(
                { length: gregorianMonthDays },
                (_, index) => index + 1,
              ).map((day) => {
                const isoDate = toIsoDate(
                  gregorian.year,
                  gregorian.month,
                  day,
                );

                return (
                  <option
                    key={day}
                    value={day}
                    disabled={isoDate < minDate}
                  >
                    {day}
                  </option>
                );
              })}
            </select>
          </label>

          <label>
            <span>Year</span>
            <select
              aria-label="Appointment year"
              value={gregorian.year}
              onChange={(event) =>
                updateGregorianDate(
                  Number(event.target.value),
                  gregorian.month,
                  gregorian.day,
                )
              }
              required
            >
              {gregorianYears.map((year) => (
                <option key={year} value={year}>
                  {year}
                </option>
              ))}
            </select>
          </label>
        </div>

        <p className="ethiopian-date-summary">
          {ENGLISH_MONTHS[gregorian.month - 1]} {gregorian.day},{" "}
          {gregorian.year}
        </p>

        <small>
          Choose a date today or later. Available appointment times will
          appear for your selected date.
        </small>
      </div>
    );
  }

  return (
    <div className="ethiopian-date-picker">
      <div className="ethiopian-date-fields">
        <label>
          <span>ዓመት</span>
          <select
            aria-label="የኢትዮጵያ ዓመት"
            value={selected.year}
            onChange={(event) =>
              updateEthiopianDate(
                Number(event.target.value),
                selected.month,
                selected.day,
              )
            }
          >
            {ethiopianYears.map((year) => (
              <option key={year} value={year}>
                {year} ዓ.ም.
              </option>
            ))}
          </select>
        </label>

        <label>
          <span>ወር</span>
          <select
            aria-label="የኢትዮጵያ ወር"
            value={selected.month}
            onChange={(event) =>
              updateEthiopianDate(
                selected.year,
                Number(event.target.value),
                selected.day,
              )
            }
          >
            {ETHIOPIAN_MONTHS_AM.map((month, index) => (
              <option key={month} value={index + 1}>
                {month}
              </option>
            ))}
          </select>
        </label>

        <label>
          <span>ቀን</span>
          <select
            aria-label="የኢትዮጵያ ቀን"
            value={selected.day}
            onChange={(event) =>
              updateEthiopianDate(
                selected.year,
                selected.month,
                Number(event.target.value),
              )
            }
          >
            {Array.from(
              { length: ethiopianMonthDays },
              (_, index) => index + 1,
            ).map((day) => (
              <option
                key={day}
                value={day}
                disabled={(() => {
                  try {
                    return (
                      ethiopianToGregorian({
                        year: selected.year,
                        month: selected.month,
                        day,
                      }) < minDate
                    );
                  } catch {
                    return true;
                  }
                })()}
              >
                {day}
              </option>
            ))}
          </select>
        </label>
      </div>

      <p className="ethiopian-date-summary">
        {ETHIOPIAN_MONTHS_AM[selected.month - 1]} {selected.day},{" "}
        {selected.year} ዓ.ም.
      </p>

      <small>
        ቀኑ በራስ-ሰር ወደ ግሪጎሪያን ቀን ይቀየራል።
      </small>
    </div>
  );
}
