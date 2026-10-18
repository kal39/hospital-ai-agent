
import type {
  ChatRequest,
  ChatResponse,
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

function isChatResponse(data: unknown): data is ChatResponse {
  if (typeof data !== "object" || data === null) {
    return false;
  }

  if (
    !("message" in data) ||
    typeof data.message !== "string" ||
    !("conversationId" in data) ||
    typeof data.conversationId !== "string" ||
    !("language" in data) ||
    (data.language !== "en" && data.language !== "am") ||
    !("detail" in data) ||
    !["short", "normal", "detailed"].includes(
      data.detail as string
    ) ||
    !("toolsUsed" in data) ||
    !Array.isArray(data.toolsUsed) ||
    !data.toolsUsed.every((tool) => typeof tool === "string") ||
    !("safetyFlag" in data) ||
    typeof data.safetyFlag !== "boolean" ||
    !("safety" in data) ||
    typeof data.safety !== "object" ||
    data.safety === null ||
    !("requiresAttention" in data.safety) ||
    typeof data.safety.requiresAttention !== "boolean"
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
