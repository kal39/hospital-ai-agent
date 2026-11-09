import { useCallback, useEffect, useMemo, useState } from "react";
import { getDoctors, getLocalDateString, type Doctor } from "../../services/appointments";
import {
  approveStaffAppointmentRequest,
  declineStaffAppointmentRequest,
  listStaffAppointmentRequests,
  type StaffAppointmentRequest,
} from "../../services/staffAppointmentRequests";

type QueueFilter = "open" | "all";

function labelStatus(status: string): string {
  const labels: Record<string, string> = {
    submitted: "Submitted",
    under_review: "Under review",
    needs_information: "Needs information",
    appointment_offered: "Appointment offered",
    appointment_confirmed: "Appointment confirmed",
    declined: "Declined",
    cancelled: "Cancelled",
  };
  return labels[status] ?? status.replaceAll("_", " ");
}

function formatDate(value?: string | null): string {
  if (!value) return "Not specified";
  const date = new Date(`${value}T00:00:00`);
  return Number.isNaN(date.getTime())
    ? value
    : date.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
}

function formatTimestamp(value: string): string {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "Something went wrong. Please try again.";
}

function isOpenRequest(request: StaffAppointmentRequest): boolean {
  return ["submitted", "under_review", "needs_information"].includes(request.status);
}

export default function StaffReview() {
  const [requests, setRequests] = useState<StaffAppointmentRequest[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [filter, setFilter] = useState<QueueFilter>("open");
  const [doctors, setDoctors] = useState<Doctor[]>([]);
  const [doctorId, setDoctorId] = useState("");
  const [appointmentDate, setAppointmentDate] = useState(getLocalDateString());
  const [appointmentTime, setAppointmentTime] = useState("09:00");
  const [declineReason, setDeclineReason] = useState("");
  const [loading, setLoading] = useState(true);
  const [working, setWorking] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const selected = requests.find((item) => item.requestId === selectedId) ?? null;

  const visibleRequests = useMemo(
    () => filter === "open" ? requests.filter(isOpenRequest) : requests,
    [filter, requests],
  );

  const loadRequests = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const result = await listStaffAppointmentRequests();
      setRequests(result);
      setSelectedId((current) =>
        current && result.some((item) => item.requestId === current)
          ? current
          : (result.find(isOpenRequest)?.requestId ?? result[0]?.requestId ?? null),
      );
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => void loadRequests(), 0);
    return () => window.clearTimeout(timer);
  }, [loadRequests]);

  useEffect(() => {
    let active = true;
    getDoctors()
      .then((result) => {
        if (active) setDoctors(result);
      })
      .catch((err: unknown) => {
        if (active) setError(errorMessage(err));
      });
    return () => { active = false; };
  }, []);

  const matchingDoctors = doctors.filter((doctor) =>
    !selected?.department ||
    doctor.department.toLowerCase() === selected.department.toLowerCase(),
  );

  const effectiveDoctorId = matchingDoctors.some((doctor) => doctor.id === doctorId)
    ? doctorId
    : (matchingDoctors[0]?.id ?? "");

  async function handleApprove(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selected) return;
    setError("");
    setSuccess("");

    if (!effectiveDoctorId) {
      setError("Select a doctor from the requested department.");
      return;
    }
    if (appointmentDate < getLocalDateString()) {
      setError("The appointment date cannot be in the past.");
      return;
    }

    const doctor = matchingDoctors.find((item) => item.id === effectiveDoctorId);
    if (!doctor) {
      setError("The selected doctor is not available for this department.");
      return;
    }

    const confirmed = window.confirm(
      `Approve this demo request and book ${doctor.name} on ${formatDate(appointmentDate)} at ${appointmentTime}?`,
    );
    if (!confirmed) return;

    setWorking(true);
    try {
      const result = await approveStaffAppointmentRequest(selected.requestId, {
        doctorId,
        date: appointmentDate,
        time: appointmentTime,
      });
      setRequests((current) => current.map((item) =>
        item.requestId === result.request.requestId ? result.request : item,
      ));
      setSuccess(`Demo appointment created successfully. Booking reference: ${result.booking.bookingId}`);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setWorking(false);
    }
  }

  async function handleDecline(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selected) return;
    const reason = declineReason.trim();

    if (reason.length < 10) {
      setError("Enter a decline explanation of at least 10 characters.");
      return;
    }

    if (!window.confirm("Decline this demo appointment request?")) return;

    setWorking(true);
    setError("");
    setSuccess("");
    try {
      const updated = await declineStaffAppointmentRequest(selected.requestId, reason);
      setRequests((current) => current.map((item) =>
        item.requestId === updated.requestId ? updated : item,
      ));
      setDeclineReason("");
      setSuccess("Demo request declined. The explanation has been recorded in its status history.");
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setWorking(false);
    }
  }

  return (
    <section className="appointment-page staff-review-page">
      <header className="appointment-intro">
        <div>
          <span className="appointment-eyebrow">STAFF WORKSPACE</span>
          <h1>Appointment request review</h1>
          <p>Review incoming requests and assign a suitable demo appointment.</p>
        </div>
        <div className="appointment-intro-icon" aria-hidden="true">✓</div>
      </header>

      <aside className="appointment-demo-notice" role="note">
        <strong>Demo staff workspace — synthetic data only</strong>
        <p>
          Requests and bookings are fictional demonstration records. This screen is not
          connected to a live hospital queue, and the demo token is not production staff
          authentication. Do not enter or share real patient information here.
        </p>
      </aside>

      {error && (
        <div className="appointment-alert appointment-alert--error" role="alert">
          <span>{error}</span>
          <button type="button" onClick={() => setError("")} aria-label="Dismiss error">×</button>
        </div>
      )}
      {success && (
        <div className="appointment-alert appointment-alert--success" role="status">
          <span>{success}</span>
          <button type="button" onClick={() => setSuccess("")} aria-label="Dismiss message">×</button>
        </div>
      )}

      <div className="staff-review-toolbar">
        <div>
          <strong>{requests.filter(isOpenRequest).length}</strong>
          <span> requests awaiting a decision</span>
        </div>
        <div className="staff-review-toolbar-actions">
          <label>
            <span className="staff-sr-only">Queue filter</span>
            <select value={filter} onChange={(event) => setFilter(event.target.value as QueueFilter)}>
              <option value="open">Open requests</option>
              <option value="all">All requests</option>
            </select>
          </label>
          <button type="button" className="appointment-refresh-button" onClick={() => void loadRequests()} disabled={loading}>
            {loading ? "Refreshing…" : "Refresh queue"}
          </button>
        </div>
      </div>

      <div className="staff-review-layout">
        <section className="appointment-panel">
          <div className="appointment-panel-heading">
            <div>
              <span className="appointment-section-label">REQUEST QUEUE</span>
              <h2>Incoming requests</h2>
            </div>
          </div>

          {loading ? (
            <div className="appointment-empty-state"><p>Loading demo queue…</p></div>
          ) : visibleRequests.length === 0 ? (
            <div className="appointment-empty-state">
              <h3>{filter === "open" ? "No open requests" : "No requests found"}</h3>
              <p>{filter === "open" ? "New patient demo requests will appear here." : "The demo queue is currently empty."}</p>
            </div>
          ) : (
            <div className="appointment-request-list">
              {visibleRequests.map((request) => (
                <button
                  type="button"
                  key={request.requestId}
                  className={`appointment-request-card ${selectedId === request.requestId ? "appointment-request-card--selected" : ""}`}
                  onClick={() => {
                    setSelectedId(request.requestId);
                    setError("");
                    setSuccess("");
                  }}
                  aria-pressed={selectedId === request.requestId}
                >
                  <span className="appointment-request-card-top">
                    <span className="appointment-request-department">{request.department || "Department not specified"}</span>
                    <span className={`appointment-status appointment-status--${request.status}`}>{labelStatus(request.status)}</span>
                  </span>
                  <span className="appointment-request-id">{request.requestId}</span>
                  <span className="appointment-request-date">Patient: {request.patientId}</span>
                  <span className="appointment-request-date">Submitted {formatTimestamp(request.submittedAt)}</span>
                  <span className="appointment-request-reason">{request.reason}</span>
                </button>
              ))}
            </div>
          )}
        </section>

        <section className="appointment-panel staff-review-detail">
          {!selected ? (
            <div className="appointment-empty-state">
              <h3>Select a request</h3>
              <p>Choose a request from the queue to review its details.</p>
            </div>
          ) : (
            <>
              <div className="appointment-panel-heading">
                <div>
                  <span className="appointment-section-label">REQUEST DETAILS</span>
                  <h2>{selected.department || "Appointment request"}</h2>
                  <p className="appointment-panel-description">{selected.requestId}</p>
                </div>
                <span className={`appointment-status appointment-status--${selected.status}`}>{labelStatus(selected.status)}</span>
              </div>

              <dl className="appointment-detail-grid">
                <div><dt>Patient reference</dt><dd>{selected.patientId}</dd></div>
                <div><dt>Preferred doctor</dt><dd>{selected.preferredDoctor || "No preference"}</dd></div>
                <div><dt>Preferred dates</dt><dd>{formatDate(selected.preferredDateStart)} – {formatDate(selected.preferredDateEnd)}</dd></div>
                <div><dt>Submitted</dt><dd>{formatTimestamp(selected.submittedAt)}</dd></div>
                <div className="appointment-detail-full"><dt>Reason for visit</dt><dd className="appointment-detail-reason">{selected.reason}</dd></div>
                {selected.bookingId && <div><dt>Demo booking reference</dt><dd>{selected.bookingId}</dd></div>}
                {selected.assignedDoctorName && <div><dt>Assigned doctor</dt><dd>{selected.assignedDoctorName}</dd></div>}
                {selected.appointmentDate && <div><dt>Appointment date</dt><dd>{formatDate(selected.appointmentDate)}</dd></div>}
                {selected.appointmentTime && <div><dt>Appointment time</dt><dd>{selected.appointmentTime}</dd></div>}
                {selected.declineReason && <div className="appointment-detail-full"><dt>Decline explanation</dt><dd>{selected.declineReason}</dd></div>}
              </dl>

              <h3 className="appointment-timeline-title">Status history</h3>
              <ol className="appointment-timeline">
                {selected.statusHistory.map((item, index) => (
                  <li key={`${item.timestamp}-${item.status}-${index}`}>
                    <span className="appointment-timeline-dot" />
                    <div className="appointment-timeline-content">
                      <strong>{labelStatus(item.status)}</strong>
                      <time>{formatTimestamp(item.timestamp)}</time>
                      <p>{item.note}</p>
                    </div>
                  </li>
                ))}
              </ol>

              {isOpenRequest(selected) ? (
                <div className="staff-review-actions">
                  <form className="appointment-form" onSubmit={handleApprove}>
                    <h3>Approve and assign appointment</h3>
                    <label htmlFor="staff-doctor">Doctor</label>
                    <select id="staff-doctor" value={effectiveDoctorId} onChange={(event) => setDoctorId(event.target.value)} required>
                      {matchingDoctors.length === 0 && <option value="">No doctors found for this department</option>}
                      {matchingDoctors.map((doctor) => <option key={doctor.id} value={doctor.id}>{doctor.name} · {doctor.location}</option>)}
                    </select>
                    <label htmlFor="staff-appointment-date">Appointment date</label>
                    <input id="staff-appointment-date" type="date" min={getLocalDateString()} value={appointmentDate} onChange={(event) => setAppointmentDate(event.target.value)} required />
                    <label htmlFor="staff-appointment-time">Available demo time</label>
                    <select id="staff-appointment-time" value={appointmentTime} onChange={(event) => setAppointmentTime(event.target.value)}>
                      <option value="09:00">09:00</option>
                      <option value="10:30">10:30</option>
                      <option value="13:00">13:00</option>
                      <option value="14:30">14:30</option>
                    </select>
                    <button className="appointment-primary-button" type="submit" disabled={working || !effectiveDoctorId || matchingDoctors.length === 0}>
                      {working ? "Processing…" : "Approve and book demo appointment"}
                    </button>
                  </form>

                  <form className="appointment-form staff-decline-form" onSubmit={handleDecline}>
                    <h3>Decline request</h3>
                    <label htmlFor="staff-decline-reason">Explanation (required)</label>
                    <textarea id="staff-decline-reason" value={declineReason} onChange={(event) => setDeclineReason(event.target.value)} minLength={10} maxLength={500} rows={3} required placeholder="Explain why this request cannot be accepted." />
                    <div className="appointment-character-count">{declineReason.length}/500 characters · Minimum 10</div>
                    <button type="submit" className="appointment-cancel-button" disabled={working || declineReason.trim().length < 10}>
                      {working ? "Processing…" : "Decline demo request"}
                    </button>
                  </form>
                </div>
              ) : (
                <p className="appointment-form-footnote">This request has already been decided and cannot be acted on again.</p>
              )}
            </>
          )}
        </section>
      </div>
    </section>
  );
}



