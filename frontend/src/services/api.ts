import type {
  ChatRequest,
  ChatResponse,
  AppointmentSlotOption,
  DoctorRecommendation,
  CareCase,
  EmergencyResponse,
} from "../types/chat";

const API_URL = (
  import.meta.env.VITE_API_URL ||
  "http://localhost:5000/api"
).replace(/\/+$/, "");

const DEMO_PATIENT_ID = import.meta.env.VITE_DEMO_PATIENT_ID;

function getErrorMessage(data: unknown): string | undefined {
  if (typeof data !== "object" || data === null) {
    return undefined;
  }

  if ("error" in data && typeof data.error === "string") {
    return data.error;
  }

  if ("detail" in data) {
    const detail = data.detail;

    if (typeof detail === "string") {
      return detail;
    }

    if (Array.isArray(detail)) {
      const messages = detail
        .map((item) => {
          if (
            typeof item === "object" &&
            item !== null &&
            "msg" in item &&
            typeof item.msg === "string"
          ) {
            return item.msg;
          }

          return undefined;
        })
        .filter((item): item is string => Boolean(item));

      if (messages.length > 0) {
        return messages.join("; ");
      }
    }
  }

  return undefined;
}

function isDoctorRecommendation(
  value: unknown
): value is DoctorRecommendation {
  if (typeof value !== "object" || value === null) {
    return false;
  }

  const doctor = value as Record<string, unknown>;

  return (
    typeof doctor.id === "string" &&
    typeof doctor.name === "string" &&
    typeof doctor.department === "string" &&
    Array.isArray(doctor.specialties) &&
    doctor.specialties.every(
      (specialty) => typeof specialty === "string"
    ) &&
    typeof doctor.location === "string" &&
    typeof doctor.isAssignedDoctor === "boolean" &&
    typeof doctor.dataSource === "string" &&
    typeof doctor.dataNotice === "string"
  );
}

function isAppointmentSlotOption(
  value: unknown
): value is AppointmentSlotOption {
  if (typeof value !== "object" || value === null) {
    return false;
  }

  const slot = value as Record<string, unknown>;

  return (
    typeof slot.doctorId === "string" &&
    typeof slot.doctorName === "string" &&
    typeof slot.department === "string" &&
    typeof slot.location === "string" &&
    typeof slot.date === "string" &&
    typeof slot.time === "string" &&
    typeof slot.slotRemainingCapacity === "number" &&
    typeof slot.dailyRemainingCapacity === "number" &&
    typeof slot.dataSource === "string"
  );
}

function isCareCase(value: unknown): value is CareCase {
  if (typeof value !== "object" || value === null) {
    return false;
  }

  const careCase = value as Record<string, unknown>;

  if (
    typeof careCase.caseId !== "string" ||
    !["emergency_concern", "urgent_concern"].includes(
      String(careCase.caseType),
    ) ||
    !["registered", "acknowledged", "in_review", "resolved"].includes(
      String(careCase.status),
    ) ||
    typeof careCase.reportedConcern !== "string" ||
    typeof careCase.createdAt !== "string" ||
    typeof careCase.updatedAt !== "string" ||
    careCase.dataSource !== "synthetic_demo" ||
    typeof careCase.dataNotice !== "string" ||
    !Array.isArray(careCase.statusHistory)
  ) {
    return false;
  }

  return careCase.statusHistory.every((entry: unknown) => {
    if (typeof entry !== "object" || entry === null) {
      return false;
    }

    const item = entry as Record<string, unknown>;

    return (
      typeof item.status === "string" &&
      typeof item.timestamp === "string" &&
      typeof item.note === "string"
    );
  });
}

function isEmergencyDirectory(
  value: unknown
): boolean {
  if (typeof value !== "object" || value === null) {
    return false;
  }

  const directory = value as Record<string, unknown>;

  if (
    directory.dataType !== "fictional_demo" ||
    typeof directory.facilityName !== "string" ||
    typeof directory.departmentName !== "string" ||
    typeof directory.floor !== "string" ||
    typeof directory.roomNumber !== "string" ||
    typeof directory.address !== "string" ||
    typeof directory.directions !== "string" ||
    !Array.isArray(directory.doctors)
  ) {
    return false;
  }

  return directory.doctors.every((doctor: unknown) => {
    if (typeof doctor !== "object" || doctor === null) {
      return false;
    }

    const item = doctor as Record<string, unknown>;

    return (
      typeof item.id === "string" &&
      typeof item.name === "string" &&
      typeof item.specialty === "string" &&
      item.profileType === "fictional_demo" &&
      item.availability === "not_provided"
    );
  });
}

function isEmergencyResponse(
  value: unknown
): value is EmergencyResponse {
  if (typeof value !== "object" || value === null) {
    return false;
  }

  const emergency = value as Record<string, unknown>;

  const nullableStringFields = [
    "hospitalName",
    "hospitalEmergencyPhone",
    "ambulanceDispatchPhone",
    "alternativeEmergencyPhone",
    "hospitalAddress",
    "emergencyDirections",
  ];

  return (
    typeof emergency.active === "boolean" &&
    ["not_configured", "partially_configured", "configured"].includes(
      String(emergency.contactAvailability)
    ) &&
    nullableStringFields.every(
      (field) =>
        emergency[field] === null ||
        typeof emergency[field] === "string"
    ) &&
    (emergency.directory === null ||
      isEmergencyDirectory(emergency.directory))
  );
}

function isChatResponse(data: unknown): data is ChatResponse {
  if (typeof data !== "object" || data === null) {
    return false;
  }

  const response = data as Record<string, unknown>;

  if (
    typeof response.message !== "string" ||
    typeof response.conversationId !== "string" ||
    (response.language !== "en" && response.language !== "am") ||
    !["short", "normal", "detailed"].includes(
      response.detail as string
    ) ||
    !Array.isArray(response.toolsUsed) ||
    !response.toolsUsed.every(
      (tool) => typeof tool === "string"
    ) ||
    typeof response.safetyFlag !== "boolean" ||
    typeof response.safety !== "object" ||
    response.safety === null ||
    !("requiresAttention" in response.safety) ||
    typeof response.safety.requiresAttention !== "boolean" ||
    !Array.isArray(response.doctorRecommendations) ||
    !response.doctorRecommendations.every(
      isDoctorRecommendation
    ) ||
    !Array.isArray(response.appointmentSlots) ||
    !response.appointmentSlots.every(
      isAppointmentSlotOption
    ) ||
    !("careCase" in response) ||
    !(
      response.careCase === null ||
      isCareCase(response.careCase)
    ) ||
    !("emergency" in response) ||
    !(
      response.emergency === null ||
      isEmergencyResponse(response.emergency)
    )
  ) {
    return false;
  }

  return true;
}

export async function sendChatMessage(
  request: ChatRequest
): Promise<ChatResponse> {
  let response: Response;

  try {
    response = await fetch(`${API_URL}/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(import.meta.env.DEV && DEMO_PATIENT_ID
          ? {
              "X-Demo-Patient-Id": DEMO_PATIENT_ID,
            }
          : {}),
      },
      body: JSON.stringify(request),
    });
  } catch {
    throw new Error(
      "Unable to connect to the hospital AI backend. " +
        "Check that the Python server is running on port 5000."
    );
  }

  let data: unknown = null;

  try {
    data = await response.json();
  } catch {
    // The response was not valid JSON.
  }

  if (!response.ok) {
    const serverMessage = getErrorMessage(data);

    if (response.status === 413) {
      throw new Error(
        "The uploaded file is too large. Please use a smaller file."
      );
    }

    if (response.status === 503) {
      throw new Error(
        serverMessage ??
          "The AI service is temporarily unavailable. Please try again."
      );
    }

    throw new Error(
      serverMessage ??
        `The hospital AI backend returned HTTP ${response.status}.`
    );
  }

  if (!isChatResponse(data)) {
    throw new Error(
      "The Python backend returned an unexpected response format."
    );
  }

  return data;
}
