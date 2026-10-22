import { useCallback, useEffect, useMemo, useState } from "react";
import {
  bookAppointment,
  cancelAppointment,
  getAvailability,
  getDepartments,
  getDoctors,
  getLocalDateString,
  getMyAppointments,
  rescheduleAppointment,
  type Appointment,
  type AppointmentSlot,
  type Doctor,
} from "../../services/appointments";

type Notice = { type: "success" | "error"; message: string };

function formatDate(value: string): string {
  if (!value) return "";
  return new Date(`${value}T12:00:00`).toLocaleDateString(undefined, {
    weekday: "short",
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

function formatTime(value: string): string {
  const [hours, minutes] = value.split(":").map(Number);
  const parsed = new Date();
  parsed.setHours(hours, minutes, 0, 0);
  return parsed.toLocaleTimeString(undefined, {
    hour: "numeric",
    minute: "2-digit",
  });
}

function statusLabel(status: string): string {
  if (status === "confirmed_demo") return "Booked · Demo";
  if (status === "cancelled_demo") return "Cancelled";
  if (status === "rescheduled_demo") return "Rescheduled";
  return status.replaceAll("_", " ");
}

export default function AppointmentBooking() {
  const today = useMemo(() => getLocalDateString(), []);
  const [departments, setDepartments] = useState<string[]>([]);
  const [doctors, setDoctors] = useState<Doctor[]>([]);
  const [department, setDepartment] = useState("");
  const [doctorId, setDoctorId] = useState("");
  const [date, setDate] = useState(today);
  const [purpose, setPurpose] = useState("");
  const [slots, setSlots] = useState<AppointmentSlot[]>([]);
  const [selectedTime, setSelectedTime] = useState("");
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [loadingInitial, setLoadingInitial] = useState(true);
  const [loadingSlots, setLoadingSlots] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [reschedulingId, setReschedulingId] = useState<string | null>(null);
  const [notice, setNotice] = useState<Notice | null>(null);

  const selectedDoctor = doctors.find((doctor) => doctor.id === doctorId);
  const departmentDoctors = doctors.filter(
    (doctor) => doctor.department === department,
  );

  const refreshAppointments = useCallback(async () => {
    setRefreshing(true);
    try {
      setAppointments(await getMyAppointments());
    } catch (error) {
      setNotice({
        type: "error",
        message:
          error instanceof Error
            ? error.message
            : "Could not load your demo appointments.",
      });
    } finally {
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    let active = true;

    async function loadInitialData() {
      setLoadingInitial(true);
      try {
        const [departmentList, doctorList, appointmentList] = await Promise.all([
          getDepartments(),
          getDoctors(),
          getMyAppointments(),
        ]);

        if (!active) return;

        setDepartments(departmentList);
        setDoctors(doctorList);
        setAppointments(appointmentList);

        const firstDoctor = doctorList[0];
        const initialDepartment =
          firstDoctor?.department ?? departmentList[0] ?? "";

        setDepartment(initialDepartment);
        setDoctorId(firstDoctor?.id ?? "");
      } catch (error) {
        if (active) {
          setNotice({
            type: "error",
            message:
              error instanceof Error
                ? error.message
                : "Could not load appointment services.",
          });
        }
      } finally {
        if (active) setLoadingInitial(false);
      }
    }

    void loadInitialData();
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    let active = true;

    async function loadSlots() {
      if (!doctorId || !date) {
        setSlots([]);
        return;
      }

      setLoadingSlots(true);
      setSelectedTime("");

      try {
        const result = await getAvailability(doctorId, date, 14);
        if (active) setSlots(result);
      } catch (error) {
        if (active) {
          setSlots([]);
          setNotice({
            type: "error",
            message:
              error instanceof Error
                ? error.message
                : "Could not load demo availability.",
          });
        }
      } finally {
        if (active) setLoadingSlots(false);
      }
    }

    void loadSlots();
    return () => {
      active = false;
    };
  }, [doctorId, date]);

  const availableSlots = slots.filter(
    (slot) =>
      slot.date === date &&
      slot.available &&
      slot.slotRemainingCapacity > 0 &&
      slot.dailyRemainingCapacity > 0,
  );

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!doctorId || !date || !selectedTime) {
      setNotice({
        type: "error",
        message: "Choose a doctor, date, and available time first.",
      });
      return;
    }

    setSubmitting(true);
    setNotice(null);

    try {
      if (reschedulingId) {
        await rescheduleAppointment(reschedulingId, {
          doctorId,
          date,
          time: selectedTime,
        });
        setNotice({
          type: "success",
          message: "Your demo appointment was rescheduled.",
        });
        setReschedulingId(null);
      } else {
        await bookAppointment({
          doctorId,
          date,
          time: selectedTime,
          purpose: purpose.trim(),
        });
        setNotice({
          type: "success",
          message: "Your fictional demo appointment was created.",
        });
        setPurpose("");
      }

      setSelectedTime("");
      await refreshAppointments();
    } catch (error) {
      setNotice({
        type: "error",
        message:
          error instanceof Error
            ? error.message
            : "The appointment action could not be completed.",
      });
    } finally {
      setSubmitting(false);
    }
  }

  async function handleCancel(appointment: Appointment) {
    const confirmed = window.confirm(
      `Cancel this fictional demo appointment with ${appointment.doctorName} on ${formatDate(appointment.date)} at ${formatTime(appointment.time)}?`,
    );

    if (!confirmed) return;

    setNotice(null);
    try {
      await cancelAppointment(appointment.bookingId);
      setNotice({
        type: "success",
        message: "The demo appointment was cancelled.",
      });
      await refreshAppointments();
    } catch (error) {
      setNotice({
        type: "error",
        message:
          error instanceof Error
            ? error.message
            : "Could not cancel this demo appointment.",
      });
    }
  }

  function startRescheduling(appointment: Appointment) {
    setReschedulingId(appointment.bookingId);
    setDepartment(appointment.department);
    setDoctorId(appointment.doctorId);
    setDate(appointment.date < today ? today : appointment.date);
    setSelectedTime("");
    setNotice({
      type: "success",
      message: "Choose a new date and time, then confirm below.",
    });

    document
      .getElementById("appointment-booking-form")
      ?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function stopRescheduling() {
    setReschedulingId(null);
    setSelectedTime("");
    setNotice(null);
  }

  const activeAppointments = appointments.filter(
    (appointment) => appointment.status === "confirmed_demo",
  );
  const previousAppointments = appointments.filter(
    (appointment) => appointment.status !== "confirmed_demo",
  );

  if (loadingInitial) {
    return (
      <main className="booking-page">
        <div className="booking-loading" role="status">
          Loading appointment services…
        </div>
      </main>
    );
  }

  return (
    <main className="booking-page">
      <section className="booking-hero">
        <div>
          <span className="booking-eyebrow">PATIENT SERVICES</span>
          <h1>Book an appointment</h1>
          <p>
            Choose a department, select a doctor, and find a suitable
            appointment time.
          </p>
        </div>
        <div className="booking-hero-icon" aria-hidden="true">
          <svg viewBox="0 0 48 48" fill="none">
            <rect
              x="7"
              y="10"
              width="34"
              height="31"
              rx="5"
              stroke="currentColor"
              strokeWidth="2.5"
            />
            <path
              d="M16 6v8M32 6v8M8 19h32M17 27h5m-2.5-2.5v5"
              stroke="currentColor"
              strokeWidth="2.5"
              strokeLinecap="round"
            />
          </svg>
        </div>
      </section>

      <aside className="booking-demo-warning" role="note">
        <span className="booking-warning-mark" aria-hidden="true">!</span>
        <div>
          <strong>Demonstration mode — fictional appointments</strong>
          <p>
            Doctors, availability, and bookings use synthetic local prototype
            data. This does not contact hospital staff or create a real hospital
            appointment. Do not use this demo for urgent medical care.
          </p>
        </div>
      </aside>

      {notice && (
        <div
          className={`booking-notice booking-notice-${notice.type}`}
          role={notice.type === "error" ? "alert" : "status"}
        >
          <span>{notice.message}</span>
          <button
            type="button"
            aria-label="Dismiss message"
            onClick={() => setNotice(null)}
          >
            ×
          </button>
        </div>
      )}

      <div className="booking-layout">
        <section className="booking-panel" id="appointment-booking-form">
          <div className="booking-panel-heading">
            <div className="booking-step">01</div>
            <div>
              <h2>{reschedulingId ? "Choose a new time" : "Find a time"}</h2>
              <p>
                {reschedulingId
                  ? "Select a replacement slot for your demo appointment."
                  : "Select a department, doctor, and available slot."}
              </p>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="booking-form">
            <label className="booking-field">
              <span>Department</span>
              <select
                value={department}
                onChange={(event) => {
                  const nextDepartment = event.target.value;
                  setDepartment(nextDepartment);
                  const firstDoctor = doctors.find(
                    (doctor) => doctor.department === nextDepartment,
                  );
                  setDoctorId(firstDoctor?.id ?? "");
                  setSelectedTime("");
                }}
                required
              >
                {departments.map((item) => (
                  <option key={item} value={item}>{item}</option>
                ))}
              </select>
            </label>

            <label className="booking-field">
              <span>Doctor</span>
              <select
                value={doctorId}
                onChange={(event) => {
                  setDoctorId(event.target.value);
                  setSelectedTime("");
                }}
                required
                disabled={departmentDoctors.length === 0}
              >
                {departmentDoctors.map((doctor) => (
                  <option key={doctor.id} value={doctor.id}>
                    {doctor.name}
                  </option>
                ))}
              </select>
            </label>

            {selectedDoctor && (
              <div className="booking-doctor-card">
                <div className="booking-doctor-avatar" aria-hidden="true">
                  {selectedDoctor.name
                    .replace(/^Dr\.\s*/i, "")
                    .split(/\s+/)
                    .slice(0, 2)
                    .map((part) => part[0])
                    .join("")}
                </div>
                <div>
                  <strong>{selectedDoctor.name}</strong>
                  <span>{selectedDoctor.department}</span>
                  <span>{selectedDoctor.location}</span>
                  {selectedDoctor.specialties.length > 0 && (
                    <small>{selectedDoctor.specialties.join(" · ")}</small>
                  )}
                </div>
              </div>
            )}

            <label className="booking-field">
              <span>Date</span>
              <input
                type="date"
                min={today}
                value={date}
                onChange={(event) => {
                  setDate(event.target.value);
                  setSelectedTime("");
                }}
                required
              />
              <small>Availability is shown for the selected date.</small>
            </label>

            <div className="booking-field">
              <span className="booking-field-label">Available time slots</span>
              {loadingSlots ? (
                <div className="booking-slot-message" role="status">
                  Checking demo availability…
                </div>
              ) : availableSlots.length > 0 ? (
                <div className="booking-slots">
                  {availableSlots.map((slot) => (
                    <button
                      className={`booking-slot ${selectedTime === slot.time ? "is-selected" : ""}`}
                      type="button"
                      key={`${slot.date}-${slot.time}`}
                      aria-pressed={selectedTime === slot.time}
                      onClick={() => setSelectedTime(slot.time)}
                    >
                      {formatTime(slot.time)}
                      <small>
                        {slot.slotRemainingCapacity} demo{" "}
                        {slot.slotRemainingCapacity === 1 ? "place" : "places"}
                      </small>
                    </button>
                  ))}
                </div>
              ) : (
                <div className="booking-slot-message">
                  No available demo slots were found for {formatDate(date)}.
                  Try another date.
                </div>
              )}
            </div>

            {!reschedulingId && (
              <label className="booking-field">
                <span>Purpose of visit <small>(optional)</small></span>
                <textarea
                  value={purpose}
                  onChange={(event) => setPurpose(event.target.value)}
                  placeholder="Briefly describe the reason for this demo appointment"
                  rows={3}
                  maxLength={200}
                />
                <small>{purpose.length}/200 characters</small>
              </label>
            )}

            <div className="booking-form-actions">
              <button
                type="submit"
                className="booking-primary-button"
                disabled={
                  submitting ||
                  loadingSlots ||
                  !doctorId ||
                  !selectedTime ||
                  !availableSlots.some((slot) => slot.time === selectedTime)
                }
              >
                {submitting
                  ? "Please wait…"
                  : reschedulingId
                    ? "Confirm demo reschedule"
                    : "Book demo appointment"}
              </button>
              {reschedulingId && (
                <button
                  type="button"
                  className="booking-secondary-button"
                  onClick={stopRescheduling}
                  disabled={submitting}
                >
                  Stop rescheduling
                </button>
              )}
            </div>
          </form>
        </section>

        <section className="booking-panel booking-my-appointments">
          <div className="booking-panel-heading">
            <div className="booking-step">02</div>
            <div>
              <h2>My appointments</h2>
              <p>Your bookings for the current demo patient.</p>
            </div>
            <button
              className="booking-refresh-button"
              type="button"
              onClick={() => void refreshAppointments()}
              disabled={refreshing}
            >
              {refreshing ? "Refreshing…" : "Refresh"}
            </button>
          </div>

          {activeAppointments.length === 0 ? (
            <div className="booking-empty">
              <div className="booking-empty-icon" aria-hidden="true">＋</div>
              <strong>No active demo appointments</strong>
              <p>Choose a slot to create your first fictional booking.</p>
            </div>
          ) : (
            <div className="booking-appointment-list">
              {activeAppointments.map((appointment) => (
                <article
                  className="booking-appointment-card"
                  key={appointment.bookingId}
                >
                  <div className="booking-appointment-top">
                    <span className="booking-status booking-status-active">
                      {statusLabel(appointment.status)}
                    </span>
                    <span className="booking-id">{appointment.bookingId}</span>
                  </div>
                  <h3>{appointment.doctorName}</h3>
                  <p className="booking-appointment-department">
                    {appointment.department}
                  </p>
                  <div className="booking-appointment-details">
                    <span>
                      <strong>Date</strong>
                      {formatDate(appointment.date)}
                    </span>
                    <span>
                      <strong>Time</strong>
                      {formatTime(appointment.time)}
                    </span>
                  </div>
                  {appointment.location && (
                    <p className="booking-location">{appointment.location}</p>
                  )}
                  {appointment.purpose && (
                    <p className="booking-purpose">
                      <strong>Purpose:</strong> {appointment.purpose}
                    </p>
                  )}
                  <div className="booking-card-actions">
                    <button
                      type="button"
                      className="booking-secondary-button"
                      onClick={() => startRescheduling(appointment)}
                    >
                      Reschedule
                    </button>
                    <button
                      type="button"
                      className="booking-cancel-button"
                      onClick={() => void handleCancel(appointment)}
                    >
                      Cancel
                    </button>
                  </div>
                </article>
              ))}
            </div>
          )}

          {previousAppointments.length > 0 && (
            <details className="booking-history">
              <summary>
                Previous and cancelled demo appointments ({previousAppointments.length})
              </summary>
              <div className="booking-appointment-list">
                {previousAppointments.map((appointment) => (
                  <article
                    className="booking-appointment-card booking-appointment-inactive"
                    key={appointment.bookingId}
                  >
                    <div className="booking-appointment-top">
                      <span className="booking-status">
                        {statusLabel(appointment.status)}
                      </span>
                      <span className="booking-id">{appointment.bookingId}</span>
                    </div>
                    <h3>{appointment.doctorName}</h3>
                    <p>
                      {formatDate(appointment.date)} · {formatTime(appointment.time)}
                    </p>
                  </article>
                ))}
              </div>
            </details>
          )}
        </section>
      </div>

      <p className="booking-bottom-note">
        Demo only · Availability and booking status are not connected to a live
        hospital scheduling system.
      </p>
    </main>
  );
}
