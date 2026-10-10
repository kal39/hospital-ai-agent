
import type { Request, Response } from "express";
import { randomUUID } from "node:crypto";
import { agentService } from "../services/agent.service.js";
import type {
  ChatImage,
  ChatRequest,
} from "../types/chat.js";

const MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024;

const ALLOWED_MIME_TYPES = [
  "image/jpeg",
  "image/png",
  "image/webp",
  "application/pdf",
] as const;

type AllowedMimeType = (typeof ALLOWED_MIME_TYPES)[number];

type FileValidationResult =
  | { valid: true; file: ChatImage }
  | { valid: false; error: string };

function validateAttachment(value: unknown): FileValidationResult {
  if (value === undefined || value === null) {
    return { valid: true, file: undefined as never };
  }

  if (typeof value !== "object" || Array.isArray(value)) {
    return {
      valid: false,
      error: "The attachment must be a valid file object.",
    };
  }

  const candidate = value as Record<string, unknown>;
  const { fileName, mimeType, dataUrl } = candidate;

  if (
    typeof fileName !== "string" ||
    fileName.trim().length === 0 ||
    fileName.length > 255
  ) {
    return {
      valid: false,
      error: "The attachment filename is invalid.",
    };
  }

  if (
    typeof mimeType !== "string" ||
    !ALLOWED_MIME_TYPES.includes(mimeType as AllowedMimeType)
  ) {
    return {
      valid: false,
      error: "Unsupported file type. Upload a JPG, PNG, WebP, or PDF file.",
    };
  }

  if (typeof dataUrl !== "string") {
    return {
      valid: false,
      error: "The attachment data is missing.",
    };
  }

  const prefix = `data:${mimeType};base64,`;

  if (!dataUrl.startsWith(prefix)) {
    return {
      valid: false,
      error: "The attachment data does not match its declared file type.",
    };
  }

  const base64 = dataUrl.slice(prefix.length);

  if (
    base64.length === 0 ||
    base64.length % 4 !== 0 ||
    !/^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$/.test(
      base64
    )
  ) {
    return {
      valid: false,
      error: "The attachment data is not valid Base64.",
    };
  }

  const fileBuffer = Buffer.from(base64, "base64");

  if (
    fileBuffer.length === 0 ||
    fileBuffer.length > MAX_FILE_SIZE_BYTES
  ) {
    return {
      valid: false,
      error: "The file must be greater than 0 bytes and no larger than 5 MB.",
    };
  }

  // Check file signatures instead of trusting the MIME type alone.
  let signatureMatches = false;

  switch (mimeType) {
    case "image/jpeg":
      signatureMatches =
        fileBuffer.length >= 3 &&
        fileBuffer[0] === 0xff &&
        fileBuffer[1] === 0xd8 &&
        fileBuffer[2] === 0xff;
      break;

    case "image/png":
      signatureMatches =
        fileBuffer.length >= 8 &&
        fileBuffer.subarray(0, 8).equals(
          Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a])
        );
      break;

    case "image/webp":
      signatureMatches =
        fileBuffer.length >= 12 &&
        fileBuffer.toString("ascii", 0, 4) === "RIFF" &&
        fileBuffer.toString("ascii", 8, 12) === "WEBP";
      break;

    case "application/pdf":
      signatureMatches =
        fileBuffer.length >= 5 &&
        fileBuffer.toString("ascii", 0, 5) === "%PDF-";
      break;
  }

  if (!signatureMatches) {
    return {
      valid: false,
      error: "The file content does not match the declared file type.",
    };
  }

  return {
    valid: true,
    file: {
      fileName,
      mimeType: mimeType as AllowedMimeType,
      dataUrl,
    },
  };
}

export async function chatController(
  req: Request,
  res: Response
): Promise<void> {
  try {
    if (!req.patient) {
      res.status(401).json({
        error: "Patient authentication required.",
      });
      return;
    }

    const body = req.body as ChatRequest;

    if (!body || typeof body !== "object" || Array.isArray(body)) {
      res.status(400).json({
        error: "A valid chat request is required.",
      });
      return;
    }

    if (typeof body.message !== "string" || body.message.trim().length === 0) {
      res.status(400).json({
        error: "Please enter a message.",
      });
      return;
    }

    if (body.message.length > 10_000) {
      res.status(400).json({
        error: "The message is too long.",
      });
      return;
    }

    const language = body.language ?? "en";

    if (language !== "en" && language !== "am") {
      res.status(400).json({
        error: "Unsupported language. Choose English or Amharic.",
      });
      return;
    }

    if (
      body.conversationId !== undefined &&
      (typeof body.conversationId !== "string" ||
        body.conversationId.length > 128)
    ) {
      res.status(400).json({
        error: "The conversation ID is invalid.",
      });
      return;
    }

    let attachment: ChatImage | undefined;

    if (body.image !== undefined && body.image !== null) {
      const validation = validateAttachment(body.image);

      if (!validation.valid) {
        res.status(400).json({ error: validation.error });
        return;
      }

      attachment = validation.file;
    }

    const conversationId = body.conversationId ?? randomUUID();

    const result = await agentService.run(
      body.message.trim(),
      {
        patientId: req.patient.patientId,
        conversationId,
      },
      language,
      attachment
    );

    res.json({
      conversationId,
      message: result.message,
      language,
      toolsUsed: result.toolsUsed,
      safetyFlag: result.safetyFlag,
    });
  } catch (error: unknown) {
    console.error("[CHAT] Request processing failed.");

    if (error instanceof Error) {
      console.error(error.message);
    }

    const message =
      error instanceof Error ? error.message : "";

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
