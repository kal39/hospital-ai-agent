
import {
  GoogleGenAI,
  type Content,
  type Part,
} from "@google/genai";

import { env } from "../config/env.js";

import { getPatientProfile } from "../tools/getPatientProfile.js";
import { getLatestLabResults } from "../tools/getLatestLabResults.js";
import { getMedications } from "../tools/getMedications.js";
import { getMedicalHistory } from "../tools/getMedicalHistory.js";
import { compareLabResults } from "../tools/compareLabResults.js";

import { hospitalToolDefinitions } from "../tools/toolDefinitions.js";

interface LLMMessage {
  role: "system" | "user" | "assistant";
  content: string;
}

interface GenerateWithToolsInput {
  systemInstruction: string;
  userMessage: string;
  conversationHistory: LLMMessage[];
  patientId: string;
}

interface GenerateWithToolsResult {
  message: string;
  toolsUsed: string[];
}

interface GeminiRequestInput {
  contents: Content[];
  systemInstruction: string;
}

const MAX_TOOL_ROUNDS = 5;
const MAX_ATTEMPTS = 2;

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function isRetryableError(error: unknown): boolean {
  const message =
    error instanceof Error ? error.message : String(error);

  const normalized = message.toLowerCase();

  return (
    normalized.includes("503") ||
    normalized.includes("unavailable") ||
    normalized.includes("high demand") ||
    normalized.includes("fetch failed") ||
    normalized.includes("connect timeout") ||
    normalized.includes("timeout") ||
    normalized.includes("429") ||
    normalized.includes("resource_exhausted")
  );
}

function toResponseObject(value: unknown): Record<string, unknown> {
  if (
    typeof value === "object" &&
    value !== null &&
    !Array.isArray(value)
  ) {
    return value as Record<string, unknown>;
  }

  return { data: value };
}

export class LLMService {
  private client: GoogleGenAI | null = null;

  constructor() {
    if (env.llmApiKey) {
      this.client = new GoogleGenAI({
        apiKey: env.llmApiKey,
      });
    }
  }

  async generateWithTools(
    input: GenerateWithToolsInput
  ): Promise<GenerateWithToolsResult> {
    if (!this.client) {
      throw new Error(
        "The hospital AI service is not configured. Check the backend environment configuration."
      );
    }

    const contents: Content[] = [];

    // Restore prior conversation messages.
    for (const message of input.conversationHistory) {
      contents.push({
        role: message.role === "assistant" ? "model" : "user",
        parts: [{ text: message.content }],
      });
    }

    contents.push({
      role: "user",
      parts: [{ text: input.userMessage }],
    });

    const toolsUsed: string[] = [];
    const toolsUsedSet = new Set<string>();

    for (let round = 0; round < MAX_TOOL_ROUNDS; round++) {
      const response = await this.generateContentWithRetry({
        contents,
        systemInstruction: input.systemInstruction,
      });

      const functionCalls = response.functionCalls ?? [];

      // If Gemini has finished without requesting another tool,
      // return its response.
      if (functionCalls.length === 0) {
        const message = response.text;

        if (!message) {
          throw new Error("Gemini returned no text response.");
        }

        return {
          message,
          toolsUsed,
        };
      }

      // CRITICAL: Preserve the original model content exactly.
      // Reconstructing functionCall parts can discard Gemini's
      // thought_signature and cause an INVALID_ARGUMENT error.
      const modelContent = response.candidates?.[0]?.content;

      if (!modelContent) {
        throw new Error(
          "Gemini requested a tool but returned no model content."
        );
      }

      contents.push(modelContent);

      const functionResponses: Part[] = [];

      for (const functionCall of functionCalls) {
        const toolName = functionCall.name;

        if (!toolName) {
          throw new Error("Gemini returned a function call without a name.");
        }

        // The patient identity always comes from the authenticated
        // backend context, never from Gemini's function arguments.
        const toolResult = this.executeTool(
          toolName,
          input.patientId
        );

        if (!toolsUsedSet.has(toolName)) {
          toolsUsedSet.add(toolName);
          toolsUsed.push(toolName);
        }

        functionResponses.push({
          functionResponse: {
            name: toolName,
            response: toResponseObject(toolResult),
          },
        });
      }

      // Return tool results as the next user turn.
      contents.push({
        role: "user",
        parts: functionResponses,
      });
    }

    throw new Error(
      `Gemini exceeded the maximum of ${MAX_TOOL_ROUNDS} tool-calling rounds.`
    );
  }

  private executeTool(
    toolName: string,
    patientId: string
  ): unknown {
    switch (toolName) {
      case "getLatestLabResults":
        return getLatestLabResults(patientId);

      case "compareLabResults":
        return compareLabResults(patientId);

      case "getMedications":
        return getMedications(patientId);

      case "getMedicalHistory":
        return getMedicalHistory(patientId);

      case "getPatientProfile":
        return getPatientProfile(patientId);

      default:
        throw new Error(
          `Unauthorized or unknown hospital tool: ${toolName}`
        );
    }
  }

  private async generateContentWithRetry({
    contents,
    systemInstruction,
  }: GeminiRequestInput) {
    if (!this.client) {
      throw new Error("Gemini client is not configured.");
    }

    let lastError: unknown;

    const models = [
      env.llmModel,
      env.llmFallbackModel,
    ].filter(
      (model, index, array) =>
        Boolean(model) && array.indexOf(model) === index
    );

    if (models.length === 0) {
      throw new Error("No Gemini model is configured.");
    }

    for (const model of models) {
      for (let attempt = 1; attempt <= MAX_ATTEMPTS; attempt++) {
        try {
          console.log(
            `Gemini request: model=${model}, attempt=${attempt}/${MAX_ATTEMPTS}`
          );

          return await this.client.models.generateContent({
            model,
            contents,
            config: {
              systemInstruction,
              tools: [
                {
                  functionDeclarations: hospitalToolDefinitions,
                },
              ],
              maxOutputTokens: 700,
              temperature: 0.2,
            },
          });
        } catch (error: unknown) {
          lastError = error;

          console.error(
            `Gemini error: model=${model}, attempt=${attempt}`,
            error
          );

          if (
            attempt < MAX_ATTEMPTS &&
            isRetryableError(error)
          ) {
            await sleep(1000);
            continue;
          }

          break;
        }
      }
    }

    if (isRetryableError(lastError)) {
      throw new Error(
        "The AI service is temporarily unavailable. Please try again in a moment."
      );
    }

    throw lastError instanceof Error
      ? lastError
      : new Error("Gemini request failed.");
  }

  async generate(messages: LLMMessage[]): Promise<string> {
    if (!this.client) {
      throw new Error(
        "The hospital AI service is not configured."
      );
    }

    const systemInstruction =
      messages.find((message) => message.role === "system")
        ?.content ?? "";

    const contents: Content[] = messages
      .filter((message) => message.role !== "system")
      .map((message) => ({
        role: message.role === "assistant" ? "model" : "user",
        parts: [{ text: message.content }],
      }));

    if (contents.length === 0) {
      contents.push({
        role: "user",
        parts: [{ text: "Hello" }],
      });
    }

    const response = await this.generateContentWithRetry({
      contents,
      systemInstruction,
    });

    if (!response.text) {
      throw new Error("Gemini returned no text.");
    }

    return response.text;
  }
}

export const llmService = new LLMService();