const API_URL = (
  import.meta.env.VITE_API_URL || "http://localhost:5000/api"
).replace(/\/+$/, "");

const DEMO_PATIENT_ID = import.meta.env.VITE_DEMO_PATIENT_ID;

export type Department = string;

export interface Doctor {
  id: string;
  name: string;
  department: string;
  specialties: string[];
  location: string;
}

export interface AppointmentSlot {
  doctorId: string;
  doctorName: string;
  department: string;
  location: string;
  date: string;
  time: string;
  status: string;
  available: boolean;
  slotRemainingCapacity: number;
  dailyRemainingCapacity: number;
  dataSource: string;
  dataNotice?: string;
}

export interface Appointment {
  bookingId: string;
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
  dataNotice?: string;
}

interface ApiOptions {
  method?: "GET" | "POST";
  body?: unknown;
}

function getHeaders(): HeadersInit {
  const headers: Record<string, string> = {
    Accept: "application/json",
  };

  if (DEMO_PATIENT_ID && import.meta.env.DEV) {
    headers["X-Demo-Patient-Id"] = DEMO_PATIENT_ID;
  }

  return headers;
}

async function requestJson<T>(
  path: string,
  options: ApiOptions = {},
): Promise<T> {
  const headers = getHeaders();

  if (options.body !== undefined) {
    (headers as Record<string, string>)["Content-Type"] = "application/json";
  }

  let response: Response;

  try {
    response = await fetch(`${API_URL}${path}`, {
      method: options.method ?? "GET",
      headers,
      body:
        options.body === undefined
          ? undefined
          : JSON.stringify(options.body),
    });
  } catch {
    throw new Error(
      "Could not connect to the appointment service. Check that the backend is running.",
    );
  }

  const payload: unknown = await response.json().catch(() => null);

  if (!response.ok) {
    let message = `Request failed (${response.status}).`;

    if (
      payload &&
      typeof payload === "object" &&
      "detail" in payload
    ) {
      const detail = (payload as { detail?: unknown }).detail;

      if (typeof detail === "string") {
        message = detail;
      } else if (Array.isArray(detail)) {
        message = detail
          .map((item) =>
            item &&
            typeof item === "object" &&
            "msg" in item
              ? String((item as { msg: unknown }).msg)
              : String(item),
          )
          .join(" ");
      }
    }

    throw new Error(message);
  }

  return payload as T;
}

export async function getDepartments(): Promise<Department[]> {
  const result = await requestJson<{ departments: Department[] }>(
    "/appointments/departments",
  );
  return result.departments;
}

export async function getDoctors(
  department?: string,
): Promise<Doctor[]> {
  const params = new URLSearchParams();

  if (department) {
    params.set("department", department);
  }

  const suffix = params.size ? `?${params.toString()}` : "";
  const result = await requestJson<{ doctors: Doctor[] }>(
    `/appointments/doctors${suffix}`,
  );

  return result.doctors;
}

export async function getAvailability(
  doctorId: string,
  startDate: string,
  days = 14,
): Promise<AppointmentSlot[]> {
  const params = new URLSearchParams({
    doctorId,
    startDate,
    days: String(days),
  });

  const result = await requestJson<{ slots: AppointmentSlot[] }>(
    `/appointments/availability?${params.toString()}`,
  );

  return result.slots;
}

export async function getMyAppointments(): Promise<Appointment[]> {
  const result = await requestJson<{ appointments: Appointment[] }>(
    "/patient/appointments",
  );

  return result.appointments;
}

export async function bookAppointment(input: {
  doctorId: string;
  date: string;
  time: string;
  purpose: string;
}): Promise<Appointment> {
  const result = await requestJson<{ booking: Appointment }>(
    "/appointments/book",
    { method: "POST", body: input },
  );

  return result.booking;
}

export async function cancelAppointment(
  bookingId: string,
): Promise<Appointment> {
  const result = await requestJson<{ booking: Appointment }>(
    `/patient/appointments/${encodeURIComponent(bookingId)}/cancel`,
    { method: "POST" },
  );

  return result.booking;
}

export async function rescheduleAppointment(
  bookingId: string,
  input: { doctorId: string; date: string; time: string },
): Promise<Appointment> {
  const result = await requestJson<{ booking: Appointment }>(
    `/patient/appointments/${encodeURIComponent(bookingId)}/reschedule`,
    { method: "POST", body: input },
  );

  return result.booking;
}

export function getLocalDateString(date = new Date()): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");

  return `${year}-${month}-${day}`;
}
