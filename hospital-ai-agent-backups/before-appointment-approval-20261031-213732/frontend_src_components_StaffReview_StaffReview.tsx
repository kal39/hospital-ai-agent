import { useCallback, useEffect, useMemo, useState } from "react";
import {
  listStaffAppointments,
  recordStaffAttendance,
  type StaffAttendanceAppointment,
} from "../../services/staffAppointmentRequests";
import type { Language } from "../../types/chat";

type Props = {
  language: Language;
};
const copy = {
  en: {
    eyebrow: "STAFF WORKSPACE",
    title: "Appointment management",
    intro: "Review appointment requests and manage patient attendance.",
    demo: "Demo staff workspace — synthetic data only",
    demoText: "All requests and appointments shown here are fictional demonstration records. This workspace is not connected to a live hospital system. Do not enter real patient information.",
    requests: "Appointment requests",
    attendance: "Attendance",
    openRequests: "requests awaiting a decision",
    refresh: "Refresh",
    refreshing: "Refreshing…",
    open: "Open requests",
    all: "All requests",
    queue: "REQUEST QUEUE",
    incoming: "Incoming requests",
    loading: "Loading…",
    noOpen: "No open requests",
    noRequests: "No requests found",
    select: "Select a request",
    selectText: "Choose a request from the list to review its details.",
    details: "REQUEST DETAILS",
    patient: "Patient reference",
    preferredDoctor: "Preferred doctor",
    noPreference: "No preference",
    preferredDates: "Preferred dates",
    submitted: "Submitted",
    reason: "Reason for visit",
    booking: "Demo booking reference",
    assigned: "Assigned doctor",
    date: "Appointment date",
    time: "Appointment time",
    declineExplanation: "Decline explanation",
    history: "Status history",
    approveTitle: "Approve and assign appointment",
    doctor: "Doctor",
    chooseDoctor: "Select a doctor",
    appointmentDate: "Appointment date",
    appointmentTime: "Appointment time",
    approve: "Approve and book demo appointment",
    decline: "Decline request",
    explanation: "Explanation (required)",
    declinePlaceholder: "Explain why this request cannot be accepted.",
    declineButton: "Decline demo request",
    processing: "Processing…",
    decided: "This request has already been decided and cannot be acted on again.",
    notSpecified: "Not specified",
    submittedStatus: "Submitted",
    underReview: "Under review",
    needsInfo: "Needs information",
    offered: "Appointment offered",
    confirmed: "Appointment confirmed",
    declined: "Declined",
    cancelled: "Cancelled",
    attendanceTitle: "Appointment attendance",
    attendanceText: "Review confirmed appointments and record whether each patient attended.",
    total: "appointments",
    search: "Search patient, doctor, department or booking reference",
    filterAll: "All appointments",
    filterPending: "Awaiting attendance",
    filterAttended: "Attended",
    filterMissed: "Missed",
    patientColumn: "Patient",
    departmentColumn: "Department",
    doctorColumn: "Doctor",
    schedule: "Scheduled",
    statusColumn: "Attendance",
    actions: "Actions",
    upcoming: "Upcoming",
    pending: "Pending",
    attended: "Attended",
    missed: "Missed",
    markAttended: "Mark attended",
    markMissed: "Mark missed",
    noAppointments: "No appointments found",
    noAppointmentsText: "Confirmed demo appointments will appear here.",
    futureNotice: "Attendance can only be recorded after the scheduled appointment time.",
    confirmAttended: "Confirm that this patient attended the appointment?",
    confirmMissed: "Confirm that this patient missed the appointment?",
    attendanceSaved: "Attendance record saved successfully.",
    patientReference: "Patient reference",
    bookingReference: "Booking reference",
    error: "Something went wrong. Please try again.",
    connection: "Could not connect to the demo backend. Check that the backend is running.",
    auth: "Staff demo authentication failed. Check the staff token and restart the frontend.",
    dismiss: "Dismiss message",
    minimum: "Minimum 10 characters",
  },
  am: {
    eyebrow: "የሰራተኞች የስራ ቦታ",
    title: "የቀጠሮ አስተዳደር",
    intro: "የቀጠሮ ጥያቄዎችን ይመልከቱ እና የታካሚዎችን መገኘት ያስተዳድሩ።",
    demo: "የሙከራ የሰራተኞች ቦታ — ሰው ሰራሽ መረጃ ብቻ",
    demoText: "እዚህ የሚታዩት ጥያቄዎችና ቀጠሮዎች ሁሉ ለሙከራ የተፈጠሩ ናቸው። ይህ ስርዓት ከእውነተኛ የሆስፒታል ስርዓት ጋር አልተገናኘም። እውነተኛ የታካሚ መረጃ አያስገቡ።",
    requests: "የቀጠሮ ጥያቄዎች",
    attendance: "የታካሚ መገኘት",
    openRequests: "ውሳኔ የሚጠብቁ ጥያቄዎች",
    refresh: "አድስ",
    refreshing: "በማደስ ላይ…",
    open: "ክፍት ጥያቄዎች",
    all: "ሁሉም ጥያቄዎች",
    queue: "የጥያቄ ዝርዝር",
    incoming: "የገቡ ጥያቄዎች",
    loading: "በመጫን ላይ…",
    noOpen: "ክፍት ጥያቄ የለም",
    noRequests: "ምንም ጥያቄ አልተገኘም",
    select: "ጥያቄ ይምረጡ",
    selectText: "ዝርዝሩን በመጠቀም የሚፈልጉትን ጥያቄ ይምረጡ።",
    details: "የጥያቄ ዝርዝር",
    patient: "የታካሚ መለያ",
    preferredDoctor: "የተመረጠ ሐኪም",
    noPreference: "ምርጫ የለም",
    preferredDates: "የተመረጡ ቀናት",
    submitted: "የቀረበበት ጊዜ",
    reason: "የጉብኝት ምክንያት",
    booking: "የሙከራ ቀጠሮ መለያ",
    assigned: "የተመደበ ሐኪም",
    date: "የቀጠሮ ቀን",
    time: "የቀጠሮ ሰዓት",
    declineExplanation: "የመከልከያ ምክንያት",
    history: "የሁኔታ ታሪክ",
    approveTitle: "ጥያቄውን ያጽድቁ እና ቀጠሮ ይመድቡ",
    doctor: "ሐኪም",
    chooseDoctor: "ሐኪም ይምረጡ",
    appointmentDate: "የቀጠሮ ቀን",
    appointmentTime: "የቀጠሮ ሰዓት",
    approve: "አጽድቅ እና የሙከራ ቀጠሮ መዝግብ",
    decline: "ጥያቄውን ከልክል",
    explanation: "ምክንያት (አስፈላጊ)",
    declinePlaceholder: "ጥያቄው ለምን መቀበል እንደማይቻል ያብራሩ።",
    declineButton: "የሙከራ ጥያቄን ከልክል",
    processing: "በሂደት ላይ…",
    decided: "ይህ ጥያቄ አስቀድሞ ውሳኔ ተሰጥቶታል።",
    notSpecified: "አልተገለጸም",
    submittedStatus: "ቀርቧል",
    underReview: "በግምገማ ላይ",
    needsInfo: "ተጨማሪ መረጃ ያስፈልጋል",
    offered: "ቀጠሮ ቀርቧል",
    confirmed: "ቀጠሮ ተረጋግጧል",
    declined: "ተከልክሏል",
    cancelled: "ተሰርዟል",
    attendanceTitle: "የቀጠሮ መገኘት መዝገብ",
    attendanceText: "የተረጋገጡ ቀጠሮዎችን ይመልከቱ እና ታካሚው መጥቶ እንደነበር ይመዝግቡ።",
    total: "ቀጠሮዎች",
    search: "ታካሚ፣ ሐኪም፣ ክፍል ወይም የቀጠሮ መለያ ይፈልጉ",
    filterAll: "ሁሉም ቀጠሮዎች",
    filterPending: "መገኘት የሚጠብቁ",
    filterAttended: "ተገኝቷል",
    filterMissed: "አልተገኘም",
    patientColumn: "ታካሚ",
    departmentColumn: "ክፍል",
    doctorColumn: "ሐኪም",
    schedule: "የቀጠሮ ጊዜ",
    statusColumn: "የመገኘት ሁኔታ",
    actions: "ተግባሮች",
    upcoming: "ወደፊት ያለ",
    pending: "በመጠባበቅ ላይ",
    attended: "ተገኝቷል",
    missed: "አልተገኘም",
    markAttended: "ተገኝቷል ብለህ መዝግብ",
    markMissed: "አልተገኘም ብለህ መዝግብ",
    noAppointments: "ቀጠሮ አልተገኘም",
    noAppointmentsText: "የተረጋገጡ የሙከራ ቀጠሮዎች እዚህ ይታያሉ።",
    futureNotice: "የመገኘት ሁኔታ መመዝገብ የሚቻለው ከቀጠሮው ጊዜ በኋላ ብቻ ነው።",
    confirmAttended: "ይህ ታካሚ በቀጠሮው ላይ እንደተገኘ ያረጋግጡ?",
    confirmMissed: "ይህ ታካሚ በቀጠሮው ላይ እንዳልተገኘ ያረጋግጡ?",
    attendanceSaved: "የመገኘት መረጃው በተሳካ ሁኔታ ተመዝግቧል።",
    patientReference: "የታካሚ መለያ",
    bookingReference: "የቀጠሮ መለያ",
    error: "ችግር ተፈጥሯል። እንደገና ይሞክሩ።",
    connection: "ከሙከራ ባክኤንድ ጋር መገናኘት አልተቻለም።",
    auth: "የሰራተኛ ሙከራ ማረጋገጫ አልተሳካም።",
    dismiss: "መልዕክቱን ዝጋ",
    minimum: "ቢያንስ 10 ቁምፊዎች",
  },
} as const;
type StaffReviewCopy = { [Key in keyof typeof copy.en]: string };

function errorMessage(error: unknown, t: StaffReviewCopy): string {
  if (!(error instanceof Error)) return t.error;
  if (error.message.includes("Could not connect")) return t.connection;
  if (error.message.includes("authentication failed")) return t.auth;
  return error.message;
}

function formatDate(value?: string | null, language: Language = "en"): string {
  if (!value) return language === "am" ? "አልተገለጸም" : "Not specified";

  const date = new Date(`${value}T00:00:00`);

  return Number.isNaN(date.getTime())
    ? value
    : date.toLocaleDateString(language === "am" ? "am-ET" : "en-ET", {
        year: "numeric",
        month: "short",
        day: "numeric",
      });
}

function attendanceStatus(
  appointment: StaffAttendanceAppointment,
  t: StaffReviewCopy,
) {
  if (appointment.status === "attended_demo") {
    return { label: t.attended, kind: "attended" };
  }

  if (appointment.status === "missed_demo") {
    return { label: t.missed, kind: "missed" };
  }

  if (appointment.status !== "confirmed_demo") {
    return { label: t.upcoming, kind: "upcoming" };
  }

  return { label: t.pending, kind: "pending" };
}

function appointmentHasPassed(
  appointment: StaffAttendanceAppointment,
): boolean {
  const scheduled = new Date(
    `${appointment.date}T${appointment.time}:00`,
  );

  return (
    !Number.isNaN(scheduled.getTime()) &&
    scheduled.getTime() <= Date.now()
  );
}

function isAttendanceEligible(
  appointment: StaffAttendanceAppointment,
): boolean {
  return (
    appointment.status === "confirmed_demo" &&
    appointmentHasPassed(appointment)
  );
}

export default function StaffReview({ language }: Props) {
  const t = copy[language];

  const [appointments, setAppointments] = useState<
    StaffAttendanceAppointment[]
  >([]);
  const [attendanceFilter, setAttendanceFilter] = useState("all");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [working, setWorking] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const loadAppointments = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const result = await listStaffAppointments();
      setAppointments(result);
    } catch (err) {
      setError(errorMessage(err, t));
    } finally {
      setLoading(false);
    }
  }, [t]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void loadAppointments();
    }, 0);

    return () => window.clearTimeout(timer);
  }, [loadAppointments]);

  const visibleAppointments = useMemo(() => {
    const query = search.trim().toLowerCase();

    return appointments
      .filter((item) =>
        ["confirmed_demo", "attended_demo", "missed_demo"].includes(
          item.status,
        ),
      )
      .filter((item) => {
        if (attendanceFilter === "pending") {
          return item.status === "confirmed_demo";
        }

        if (attendanceFilter === "attended") {
          return item.status === "attended_demo";
        }

        if (attendanceFilter === "missed") {
          return item.status === "missed_demo";
        }

        return true;
      })
      .filter(
        (item) =>
          !query ||
          [
            item.patientId,
            item.doctorName,
            item.department,
            item.bookingId,
          ].some((value) => value?.toLowerCase().includes(query)),
      )
      .sort((a, b) =>
        `${b.date} ${b.time}`.localeCompare(`${a.date} ${a.time}`),
      );
  }, [appointments, attendanceFilter, search]);

  async function handleAttendance(
    appointment: StaffAttendanceAppointment,
    outcome: "attended" | "missed",
  ) {
    if (!isAttendanceEligible(appointment)) return;

    const confirmed = window.confirm(
      outcome === "attended" ? t.confirmAttended : t.confirmMissed,
    );

    if (!confirmed) return;

    setWorking(true);
    setError("");
    setSuccess("");

    try {
      const updated = await recordStaffAttendance(
        appointment.bookingId,
        outcome,
      );

      setAppointments((current) =>
        current.map((item) =>
          item.bookingId === updated.bookingId ? updated : item,
        ),
      );

      setSuccess(t.attendanceSaved);
    } catch (err) {
      setError(errorMessage(err, t));
    } finally {
      setWorking(false);
    }
  }

  const confirmedCount = appointments.filter(
    (item) => item.status === "confirmed_demo",
  ).length;

  return (
    <section className="appointment-page staff-review-page">
      <header className="appointment-intro">
        <div>
          <span className="appointment-eyebrow">{t.eyebrow}</span>
          <h1>{t.title}</h1>
          <p>{t.attendanceText}</p>
        </div>
        <div className="appointment-intro-icon" aria-hidden="true">
          ✓
        </div>
      </header>

      <aside className="appointment-demo-notice" role="note">
        <strong>{t.demo}</strong>
        <p>{t.demoText}</p>
      </aside>

      {error && (
        <div
          className="appointment-alert appointment-alert--error"
          role="alert"
        >
          <span>{error}</span>
          <button
            type="button"
            onClick={() => setError("")}
            aria-label={t.dismiss}
          >
            ×
          </button>
        </div>
      )}

      {success && (
        <div
          className="appointment-alert appointment-alert--success"
          role="status"
        >
          <span>{success}</span>
          <button
            type="button"
            onClick={() => setSuccess("")}
            aria-label={t.dismiss}
          >
            ×
          </button>
        </div>
      )}

      <div className="staff-review-toolbar">
        <div>
          <strong>{confirmedCount}</strong>
          <span> {t.total}</span>
        </div>

        <button
          type="button"
          className="appointment-refresh-button"
          onClick={() => void loadAppointments()}
          disabled={loading}
        >
          {loading ? t.refreshing : t.refresh}
        </button>
      </div>

      <section className="appointment-panel staff-attendance-panel">
        <div className="appointment-panel-heading">
          <div>
            <span className="appointment-section-label">
              {t.attendance}
            </span>
            <h2>{t.attendanceTitle}</h2>
            <p className="appointment-panel-description">
              {t.attendanceText}
            </p>
          </div>
        </div>

        <div className="staff-attendance-controls">
          <input
            type="search"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder={t.search}
            aria-label={t.search}
          />

          <select
            value={attendanceFilter}
            onChange={(event) => setAttendanceFilter(event.target.value)}
            aria-label={t.statusColumn}
          >
            <option value="all">{t.filterAll}</option>
            <option value="pending">{t.filterPending}</option>
            <option value="attended">{t.filterAttended}</option>
            <option value="missed">{t.filterMissed}</option>
          </select>
        </div>

        {loading ? (
          <div className="appointment-empty-state">
            <p>{t.loading}</p>
          </div>
        ) : visibleAppointments.length === 0 ? (
          <div className="appointment-empty-state">
            <h3>{t.noAppointments}</h3>
            <p>{t.noAppointmentsText}</p>
          </div>
        ) : (
          <div className="staff-attendance-table-wrap">
            <table className="staff-attendance-table">
              <thead>
                <tr>
                  <th>{t.patientColumn}</th>
                  <th>{t.departmentColumn}</th>
                  <th>{t.doctorColumn}</th>
                  <th>{t.schedule}</th>
                  <th>{t.statusColumn}</th>
                  <th>{t.actions}</th>
                </tr>
              </thead>

              <tbody>
                {visibleAppointments.map((appointment) => {
                  const status = attendanceStatus(appointment, t);
                  const eligible = isAttendanceEligible(appointment);

                  return (
                    <tr key={appointment.bookingId}>
                      <td>
                        <strong>{appointment.patientId}</strong>
                        <small>{appointment.bookingId}</small>
                      </td>

                      <td>{appointment.department}</td>
                      <td>{appointment.doctorName}</td>

                      <td>
                        <strong>
                          {formatDate(appointment.date, language)}
                        </strong>
                        <small>{appointment.time}</small>
                      </td>

                      <td>
                        <span
                          className={`staff-attendance-status staff-attendance-status--${status.kind}`}
                        >
                          {status.label}
                        </span>
                      </td>

                      <td>
                        {eligible ? (
                          <div className="staff-attendance-actions">
                            <button
                              type="button"
                              disabled={working}
                              onClick={() =>
                                void handleAttendance(
                                  appointment,
                                  "attended",
                                )
                              }
                            >
                              {t.markAttended}
                            </button>

                            <button
                              type="button"
                              disabled={working}
                              onClick={() =>
                                void handleAttendance(
                                  appointment,
                                  "missed",
                                )
                              }
                            >
                              {t.markMissed}
                            </button>
                          </div>
                        ) : appointment.status === "confirmed_demo" ? (
                          <span className="staff-attendance-upcoming">
                            {t.futureNotice}
                          </span>
                        ) : (
                          <span className="staff-attendance-recorded">
                            —
                          </span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </section>
  );
}
