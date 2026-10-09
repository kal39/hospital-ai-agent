import type {
  ChatRequest,
  ChatResponse,
} from "../types/chat";

const API_URL =
  import.meta.env.VITE_API_URL ||
  "http://localhost:5000/api";

export async function sendChatMessage(
  request: ChatRequest
): Promise<ChatResponse> {
  try {
    const response = await fetch(
      `${API_URL}/chat`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(request),
      }
    );

    let data: unknown = null;

    try {
      data = await response.json();
    } catch {
      // Response was not valid JSON.
    }

    if (!response.ok) {
      if (
        typeof data === "object" &&
        data !== null &&
        "error" in data &&
        typeof data.error === "string"
      ) {
        throw new Error(data.error);
      }

      if (response.status === 503) {
        throw new Error(
          "The AI service is temporarily unavailable. Please try again in a moment."
        );
      }

      throw new Error(
        "The hospital AI assistant could not process your request."
      );
    }

    return data as ChatResponse;
  } catch (error) {
    if (error instanceof Error) {
      throw error;
    }

    throw new Error(
      "Unable to communicate with the hospital AI assistant."
    );
  }
}