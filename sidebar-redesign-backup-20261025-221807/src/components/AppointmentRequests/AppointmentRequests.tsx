import { useCallback, useEffect, useState } from "react";

import {
  cancelAppointmentRequest,
  canCancelAppointmentRequest,
  createAppointmentRequest,
  listAppointmentRequests,
  type AppointmentRequest,
  type AppointmentRequestStatus,
} from "../../services/appointmentRequests";

const DEPARTMENTS = [
  "General Medicine",
  "Cardiology",
  "Dermatology",
  "Neurology",
  "Orthopedics",
  "Pediatrics",
  "Gynecology",
  "Ophthalmology",
  "Dental",
  "Other",
];

function formatDate(value: string | null | undefined): string {
  if (!value) return "Not specified";

  const parsed = new Date(`${value}T00:00:00`);

  if (Number.isNaN(parsed.getTime())) return value;

  return parsed.toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

function formatTimestamp(value: string): string {
  const parsed = new Date(value);

  if (Number.isNaN(parsed.getTime())) return value;

  return parsed.toLocaleString();
}

function getStatusLabel(status: AppointmentRequestStatus): string {
  const labels: Record<AppointmentRequestStatus, string> = {
    submitted: "Submitted",
    under_review: "Under review",
    needs_information: "Needs information",
    appointment_offered: "Appointment offered",
    declined: "Declined",
    cancelled: "Cancelled",
    appointment_confirmed: "Appointment confirmed",
  };

  return labels[status] ?? status;
}

function getStatusClass(status: AppointmentRequestStatus): string {
  return `appointment-status appointment-status--${status}`;
}

function getErrorMessage(error: unknown): string {
  return error instanceof Error
    ? error.message
    : "Something went wrong. Please try again.";
}

export default function AppointmentRequests() {
  const [requests, setRequests] = useState<AppointmentRequest[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const [department, setDepartment] = useState("General Medicine");
  const [preferredDoctor, setPreferredDoctor] = useState("");
  const [preferredDateStart, setPreferredDateStart] = useState("");
  const [preferredDateEnd, setPreferredDateEnd] = useState("");
  const [reason, setReason] = useState("");

  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [cancellingId, setCancellingId] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const selectedRequest =
    requests.find((request) => request.requestId === selectedId) ?? null;

  const loadRequests = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const result = await listAppointmentRequests();
      setRequests(result);

      setSelectedId((current) => {
        if (current && result.some((item) => item.requestId === current)) {
          return current;
        }

        return result[0]?.requestId ?? null;
      });
    } catch (loadError) {
      setError(getErrorMessage(loadError));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const timerId = window.setTimeout(() => {
      void loadRequests();
    }, 0);

    return () => {
      window.clearTimeout(timerId);
    };
  }, [loadRequests]);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setSuccess("");

    const trimmedReason = reason.trim();

    if (trimmedReason.length < 10) {
      setError("Please describe your reason in at least 10 characters.");
      return;
    }

    if (
      preferredDateStart &&
      preferredDateEnd &&
      preferredDateEnd < preferredDateStart
    ) {
      setError("The end date must be on or after the start date.");
      return;
    }

    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const todayString = [
      today.getFullYear(),
      String(today.getMonth() + 1).padStart(2, "0"),
      String(today.getDate()).padStart(2, "0"),
    ].join("-");

    if (
      (preferredDateStart && preferredDateStart < todayString) ||
      (preferredDateEnd && preferredDateEnd < todayString)
    ) {
      setError("Preferred dates cannot be in the past.");
      return;
    }

    setSubmitting(true);

    try {
      const created = await createAppointmentRequest({
        department,
        preferredDoctor,
        preferredDateStart,
        preferredDateEnd,
        reason: trimmedReason,
      });

      setRequests((current) => [
        created,
        ...current.filter(
          (item) => item.requestId !== created.requestId,
        ),
      ]);

      setSelectedId(created.requestId);
      setPreferredDoctor("");
      setPreferredDateStart("");
      setPreferredDateEnd("");
      setReason("");
      setSuccess(
        "Your demo request was submitted locally. It has not been sent to hospital staff.",
      );
    } catch (submitError) {
      setError(getErrorMessage(submitError));
    } finally {
      setSubmitting(false);
    }
  }

  async function handleCancel(request: AppointmentRequest) {
    const confirmed = window.confirm(
      "Cancel this demo request? This action cannot be undone.",
    );

    if (!confirmed) return;

    setError("");
    setSuccess("");
    setCancellingId(request.requestId);

    try {
      const updated = await cancelAppointmentRequest(request.requestId);

      setRequests((current) =>
        current.map((item) =>
          item.requestId === updated.requestId ? updated : item,
        ),
      );

      setSelectedId(updated.requestId);
      setSuccess("The demo request has been cancelled.");
    } catch (cancelError) {
      setError(getErrorMessage(cancelError));
    } finally {
      setCancellingId(null);
    }
  }

  return (
    <main className="appointment-page">
      <section className="appointment-intro">
        <div>
          <span className="appointment-eyebrow">PATIENT SERVICES</span>
          <h1>Appointment requests</h1>
          <p>
            Submit a request for a visit and review the requests created in
            this demonstration.
          </p>
        </div>
        <div className="appointment-intro-icon" aria-hidden="true">
          +
        </div>
      </section>

      <section className="appointment-demo-notice" role="note">
        <strong>Demonstration mode — please read</strong>
        <p>
          These are synthetic demo requests stored temporarily in local
          memory. They are not sent to hospital staff, are not reviewed by
          a clinician, and do not create or confirm a real appointment.
          Requests are lost when the backend restarts. Do not enter
          sensitive personal medical information.
        </p>
      </section>

      {error && (
        <div className="appointment-alert appointment-alert--error" role="alert">
          <span>{error}</span>
          <button type="button" onClick={() => setError("")} aria-label="Dismiss error">
            ×
          </button>
        </div>
      )}

      {success && (
        <div className="appointment-alert appointment-alert--success" role="status">
          <span>{success}</span>
          <button type="button" onClick={() => setSuccess("")} aria-label="Dismiss message">
            ×
          </button>
        </div>
      )}

      <div className="appointment-layout">
        <section className="appointment-panel">
          <div className="appointment-panel-heading">
            <div>
              <span className="appointment-section-label">NEW REQUEST</span>
              <h2>Request an appointment</h2>
            </div>
            <span className="appointment-heading-icon" aria-hidden="true">
              +
            </span>
          </div>

          <form className="appointment-form" onSubmit={handleSubmit}>
            <label htmlFor="appointment-department">
              Department <span className="appointment-required">*</span>
            </label>
            <select
              id="appointment-department"
              value={department}
              onChange={(event) => setDepartment(event.target.value)}
              required
            >
              {DEPARTMENTS.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </select>

            <label htmlFor="appointment-doctor">
              Preferred doctor <span className="appointment-optional">(optional)</span>
            </label>
            <input
              id="appointment-doctor"
              type="text"
              value={preferredDoctor}
              onChange={(event) => setPreferredDoctor(event.target.value)}
              maxLength={120}
              placeholder="Enter a doctor's name, if preferred"
            />

            <div className="appointment-date-grid">
              <div>
                <label htmlFor="appointment-start">Preferred date from</label>
                <input
                  id="appointment-start"
                  type="date"
                  value={preferredDateStart}
                  min={new Date().toLocaleDateString("en-CA")}
                  onChange={(event) => setPreferredDateStart(event.target.value)}
                />
              </div>
              <div>
                <label htmlFor="appointment-end">Preferred date to</label>
                <input
                  id="appointment-end"
                  type="date"
                  value={preferredDateEnd}
                  min={preferredDateStart || new Date().toLocaleDateString("en-CA")}
                  onChange={(event) => setPreferredDateEnd(event.target.value)}
                />
              </div>
            </div>

            <label htmlFor="appointment-reason">
              Reason for the request <span className="appointment-required">*</span>
            </label>
            <textarea
              id="appointment-reason"
              value={reason}
              onChange={(event) => setReason(event.target.value)}
              minLength={10}
              maxLength={2000}
              rows={5}
              required
              placeholder="Briefly describe why you are requesting an appointment. Avoid sensitive details in this demo."
            />
            <div className="appointment-character-count">
              {reason.length}/2000 characters · Minimum 10
            </div>

            <button
              className="appointment-primary-button"
              type="submit"
              disabled={submitting}
            >
              {submitting ? "Submitting request..." : "Submit demo request"}
            </button>

            <p className="appointment-form-footnote">
              Submitting this form does not book a visit or replace medical
              advice.
            </p>
          </form>
        </section>

        <section className="appointment-panel appointment-history-panel">
          <div className="appointment-panel-heading">
            <div>
              <span className="appointment-section-label">YOUR ACTIVITY</span>
              <h2>Request history</h2>
              <p className="appointment-panel-description">
                {requests.length} {requests.length === 1 ? "request" : "requests"} in this demo
              </p>
            </div>
            <button
              type="button"
              className="appointment-refresh-button"
              onClick={() => void loadRequests()}
              disabled={loading}
            >
              {loading ? "Loading..." : "Refresh"}
            </button>
          </div>

          {loading ? (
            <div className="appointment-empty-state">
              <span className="appointment-loading-spinner" />
              <p>Loading request history...</p>
            </div>
          ) : requests.length === 0 ? (
            <div className="appointment-empty-state">
              <span className="appointment-empty-icon" aria-hidden="true">
                ▤
              </span>
              <h3>No requests yet</h3>
              <p>
                Submit the form to create your first demonstration request.
              </p>
            </div>
          ) : (
            <div className="appointment-request-list">
              {requests.map((request) => (
                <button
                  type="button"
                  key={request.requestId}
                  className={`appointment-request-card ${
                    selectedId === request.requestId
                      ? "appointment-request-card--selected"
                      : ""
                  }`}
                  onClick={() => setSelectedId(request.requestId)}
                  aria-pressed={selectedId === request.requestId}
                >
                  <div className="appointment-request-card-top">
                    <span className="appointment-request-department">
                      {request.department || "Department not specified"}
                    </span>
                    <span className={getStatusClass(request.status)}>
                      {getStatusLabel(request.status)}
                    </span>
                  </div>
                  <span className="appointment-request-id">
                    {request.requestId}
                  </span>
                  <span className="appointment-request-date">
                    Submitted {formatTimestamp(request.submittedAt)}
                  </span>
                  <span className="appointment-request-reason">
                    {request.reason}
                  </span>
                </button>
              ))}
            </div>
          )}

          {!loading && selectedRequest && (
            <section className="appointment-detail">
              <div className="appointment-detail-heading">
                <div>
                  <span className="appointment-section-label">
                    SELECTED REQUEST
                  </span>
                  <h3>Request details</h3>
                </div>
                <span className={getStatusClass(selectedRequest.status)}>
                  {getStatusLabel(selectedRequest.status)}
                </span>
              </div>

              <dl className="appointment-detail-grid">
                <div>
                  <dt>Request ID</dt>
                  <dd>{selectedRequest.requestId}</dd>
                </div>
                <div>
                  <dt>Department</dt>
                  <dd>{selectedRequest.department || "Not specified"}</dd>
                </div>
                <div>
                  <dt>Preferred doctor</dt>
                  <dd>{selectedRequest.preferredDoctor || "No preference"}</dd>
                </div>
                <div>
                  <dt>Preferred date range</dt>
                  <dd>
                    {formatDate(selectedRequest.preferredDateStart)}
                    {selectedRequest.preferredDateEnd
                      ? ` – ${formatDate(selectedRequest.preferredDateEnd)}`
                      : ""}
                  </dd>
                </div>
                <div className="appointment-detail-full">
                  <dt>Reason</dt>
                  <dd className="appointment-detail-reason">
                    {selectedRequest.reason}
                  </dd>
                </div>
              </dl>

              <h4 className="appointment-timeline-title">Status history</h4>
              <ol className="appointment-timeline">
                {selectedRequest.statusHistory.map((item, index) => (
                  <li key={`${item.timestamp}-${item.status}-${index}`}>
                    <span className="appointment-timeline-dot" />
                    <div className="appointment-timeline-content">
                      <strong>{getStatusLabel(item.status)}</strong>
                      <time>{formatTimestamp(item.timestamp)}</time>
                      <p>{item.note}</p>
                    </div>
                  </li>
                ))}
              </ol>

              {canCancelAppointmentRequest(selectedRequest.status) && (
                <button
                  type="button"
                  className="appointment-cancel-button"
                  onClick={() => void handleCancel(selectedRequest)}
                  disabled={cancellingId === selectedRequest.requestId}
                >
                  {cancellingId === selectedRequest.requestId
                    ? "Cancelling..."
                    : "Cancel demo request"}
                </button>
              )}

              {selectedRequest.status === "appointment_confirmed" && (
                <p className="appointment-form-footnote">
                  This status would represent a confirmed appointment in a
                  future integrated system. This demo does not connect to
                  real hospital appointments.
                </p>
              )}
            </section>
          )}
        </section>
      </div>
    </main>
  );
}
