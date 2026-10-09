
import type { Request, Response } from "express";
import { randomUUID } from "node:crypto";
import { agentService } from "../services/agent.service.js";
import type { ChatRequest } from "../types/chat.js";

export async function chatController(
  req: Request,
  res: Response
): Promise<void> {
  console.log("[CHAT DEBUG] Request reached chatController.");

  try {
    const body = req.body as ChatRequest;

    if (!req.patient) {
      console.error("[CHAT DEBUG] Patient authentication missing.");

      res.status(401).json({
        error: "Patient authentication required.",
      });
      return;
    }

    const conversationId = body.conversationId ?? randomUUID();
    const language = body.language ?? "en";

    console.log("[CHAT DEBUG] Request validation passed.");
    console.log("[CHAT DEBUG] Calling agentService.run...");

const result = await agentService.run(
  body.message,
  {
    patientId: req.patient.patientId,
    conversationId,
  },
  language,
  body.image
);

    console.log("[CHAT DEBUG] Agent service completed successfully.");

    res.json({
      conversationId,
      message: result.message,
      language,
      toolsUsed: result.toolsUsed,
      safetyFlag: result.safetyFlag,
    });
  } catch (error: unknown) {
    console.error("[CHAT DEBUG] Controller caught an exception:");

    if (error instanceof Error) {
      console.error(error.stack ?? error.message);
    } else {
      console.error(error);
    }

    const message =
      error instanceof Error
        ? error.message
        : "Unknown backend error";

    const isTemporaryAIError = message.includes(
      "AI service is temporarily unavailable"
    );

    res.status(isTemporaryAIError ? 503 : 500).json({
      error: isTemporaryAIError
        ? message
        : "The AI assistant could not process your request.",
    });
  }
}