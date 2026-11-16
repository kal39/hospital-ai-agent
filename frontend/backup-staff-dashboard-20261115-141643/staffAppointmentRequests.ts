import type {
  AppointmentRequestStatus,
  AppointmentRequestHistoryItem,
} from "./appointmentRequests";

import type {
  Appointment,
  AppointmentSlot,
  Doctor,
} from "./appointments";

export interface StaffAppointmentRequest {
  requestId: string;
  patientId: string;
  department: string | null;
  preferredDoctor: string | null;
  preferredDateStart: string | null;
  preferredDateEnd: string | null;
  reason: string;
  status: AppointmentRequestStatus;
  submittedAt: string;
  updatedAt: string;
  statusHistory: AppointmentRequestHistoryItem[];
  declineReason?: string;
  bookingId?: string;
  assignedDoctorName?: string;
  appointmentDate?: string;
  appointmentTime?: string;
}

const API_URL = (
  import.meta.env.VITE_API_URL || "http://localhost:5000/api"
).replace(/\/+$/, "");

const STAFF_TOKEN = import.meta.env.VITE_DEMO_STAFF_TOKEN;

function staffHeaders(): HeadersInit {
  return {
    Accept: "application/json",
    "Content-Type": "application/json",
    ...(import.meta.env.DEV && STAFF_TOKEN
      ? { "X-Demo-Staff-Token": STAFF_TOKEN }
      : {}),
  };
}

async function requestJson<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  let response: Response;

  try {
    response = await fetch(`${API_URL}${path}`, {
      ...options,
      headers: { ...staffHeaders(), ...options.headers },
    });
  } catch {
    throw new Error(
      "Could not connect to the demo backend. Check that the backend is running.",
    );
  }

  const payload: unknown = await response.json().catch(() => null);

  if (!response.ok) {
    let message = `Request failed (${response.status}).`;

    if (payload && typeof payload === "object" && "detail" in payload) {
      const detail = (payload as { detail: unknown }).detail;

      if (typeof detail === "string") {
        message = detail;
      } else if (Array.isArray(detail)) {
        message = detail
          .map((item) =>
            item && typeof item === "object" && "msg" in item
              ? String(item.msg)
              : String(item),
          )
          .join(" ");
      }
    }

    if (response.status === 401) {
      message =
        "Staff demo authentication failed. Check the staff token and restart the frontend.";
    }

    throw new Error(message);
  }

  return payload as T;
}

/* -------------------------------------------------------------------------- */
/* Appointment request review                                                 */
/* -------------------------------------------------------------------------- */

export async function listStaffAppointmentRequests(): Promise<
  StaffAppointmentRequest[]
> {
  const result = await requestJson<{
    requests: StaffAppointmentRequest[];
  }>("/staff/appointment-requests");

  return result.requests;
}

export async function approveStaffAppointmentRequest(
  requestId: string,
  input: {
    doctorId: string;
    date: string;
    time: string;
  },
): Promise<{
  request: StaffAppointmentRequest;
  booking: Appointment;
}> {
  return requestJson(
    `/staff/appointment-requests/${encodeURIComponent(requestId)}/approve`,
    {
      method: "POST",
      body: JSON.stringify(input),
    },
  );
}

export async function declineStaffAppointmentRequest(
  requestId: string,
  reason: string,
): Promise<StaffAppointmentRequest> {
  const result = await requestJson<{
    request: StaffAppointmentRequest;
  }>(
    `/staff/appointment-requests/${encodeURIComponent(requestId)}/decline`,
    {
      method: "POST",
      body: JSON.stringify({ reason }),
    },
  );

  return result.request;
}

/* -------------------------------------------------------------------------- */
/* Staff-only doctor directory and availability                              */
/* -------------------------------------------------------------------------- */

export async function listStaffDoctors(
  department?: string,
): Promise<Doctor[]> {
  const params = new URLSearchParams();

  if (department?.trim()) {
    params.set("department", department.trim());
  }

  const query = params.toString();
  const result = await requestJson<{ doctors: Doctor[] }>(
    `/staff/doctors${query ? `?${query}` : ""}`,
  );

  return result.doctors;
}

export async function getStaffAvailability(
  doctorId: string,
  startDate: string,
  days = 14,
): Promise<AppointmentSlot[]> {
  const params = new URLSearchParams({
    doctorId,
    startDate,
    days: String(days),
  });

  const result = await requestJson<{
    slots: AppointmentSlot[];
  }>(`/staff/availability?${params.toString()}`);

  return result.slots;
}

export type { Doctor, AppointmentSlot };

/* -------------------------------------------------------------------------- */
/* Staff attendance                                                           */
/* -------------------------------------------------------------------------- */

export interface StaffAttendanceAppointment {
  bookingId: string;
  patientId: string;
  doctorId: string;
  doctorName: string;
  department: string;
  location: string;
  date: string;
  time: string;
  purpose: string;
  status: string;
  createdAt?: string;
  updatedAt?: string;
}

export async function listStaffAppointments(): Promise<
  StaffAttendanceAppointment[]
> {
  const result = await requestJson<{
    appointments: StaffAttendanceAppointment[];
  }>("/staff/appointments");

  return result.appointments;
}

export async function recordStaffAttendance(
  bookingId: string,
  outcome: "attended" | "missed",
): Promise<StaffAttendanceAppointment> {
  const result = await requestJson<{
    booking: StaffAttendanceAppointment;
  }>(
    `/staff/appointments/${encodeURIComponent(bookingId)}/attendance`,
    {
      method: "POST",
      body: JSON.stringify({ outcome }),
    },
  );

  return result.booking;
}
