export type AppointmentRequestStatus =
  | "submitted"
  | "under_review"
  | "needs_information"
  | "appointment_offered"
  | "declined"
  | "cancelled"
  | "appointment_confirmed";

export interface AppointmentRequestHistoryItem {
  status: AppointmentRequestStatus;
  timestamp: string;
  note: string;
}

export interface AppointmentRequest {
  requestId: string;
  department: string | null;
  preferredDoctor: string | null;
  preferredDateStart: string | null;
  preferredDateEnd: string | null;
  reason: string;
  status: AppointmentRequestStatus;
  submittedAt: string;
  updatedAt: string;
  statusHistory: AppointmentRequestHistoryItem[];
  dataSource: string;
  dataNotice: string;
}

export interface CreateAppointmentRequestInput {
  department?: string;
  preferredDoctor?: string;
  preferredDateStart?: string;
  preferredDateEnd?: string;
  reason: string;
}

interface AppointmentRequestResponse {
  request: AppointmentRequest;
}

interface AppointmentRequestListResponse {
  requests: AppointmentRequest[];
  dataSource: string;
}

const API_URL = (
  import.meta.env.VITE_API_URL || "http://localhost:5000/api"
).replace(/\/+$/, "");

const DEMO_PATIENT_ID = import.meta.env.VITE_DEMO_PATIENT_ID;

const CANCELLABLE_STATUSES: AppointmentRequestStatus[] = [
  "submitted",
  "under_review",
  "needs_information",
  "appointment_offered",
];

export function canCancelAppointmentRequest(
  status: AppointmentRequestStatus,
): boolean {
  return CANCELLABLE_STATUSES.includes(status);
}

function getHeaders(): HeadersInit {
  return {
    "Content-Type": "application/json",
    ...(import.meta.env.DEV && DEMO_PATIENT_ID
      ? { "X-Demo-Patient-Id": DEMO_PATIENT_ID }
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
      headers: {
        ...getHeaders(),
        ...options.headers,
      },
    });
  } catch {
    throw new Error(
      "Could not connect to the demo server. Make sure the backend is running.",
    );
  }

  if (!response.ok) {
    let message = `Request failed (${response.status}).`;

    try {
      const data: unknown = await response.json();

      if (
        typeof data === "object" &&
        data !== null &&
        "detail" in data
      ) {
        const detail = (data as { detail: unknown }).detail;

        if (typeof detail === "string") {
          message = detail;
        } else if (Array.isArray(detail)) {
          message = detail
            .map((item) => {
              if (
                typeof item === "object" &&
                item !== null &&
                "msg" in item
              ) {
                return String(item.msg);
              }

              return String(item);
            })
            .join(" ");
        }
      }
    } catch {
      // Use the fallback message.
    }

    throw new Error(message);
  }

  return (await response.json()) as T;
}

export async function createAppointmentRequest(
  input: CreateAppointmentRequestInput,
): Promise<AppointmentRequest> {
  const result = await requestJson<AppointmentRequestResponse>(
    "/patient/appointment-requests",
    {
      method: "POST",
      body: JSON.stringify({
        department: input.department?.trim() || null,
        preferredDoctor: input.preferredDoctor?.trim() || null,
        preferredDateStart: input.preferredDateStart || null,
        preferredDateEnd: input.preferredDateEnd || null,
        reason: input.reason.trim(),
      }),
    },
  );

  return result.request;
}

export async function listAppointmentRequests(): Promise<
  AppointmentRequest[]
> {
  const result = await requestJson<AppointmentRequestListResponse>(
    "/patient/appointment-requests",
  );

  return result.requests;
}

export async function getAppointmentRequest(
  requestId: string,
): Promise<AppointmentRequest> {
  const result = await requestJson<AppointmentRequestResponse>(
    `/patient/appointment-requests/${encodeURIComponent(requestId)}`,
  );

  return result.request;
}

export async function cancelAppointmentRequest(
  requestId: string,
): Promise<AppointmentRequest> {
  const result = await requestJson<AppointmentRequestResponse>(
    `/patient/appointment-requests/${encodeURIComponent(requestId)}/cancel`,
    { method: "POST" },
  );

  return result.request;
}
