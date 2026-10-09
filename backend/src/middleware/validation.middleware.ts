import { NextFunction, Request, Response } from "express";
import { z } from "zod";
import { env } from "../config/env.js";

const chatSchema = z.object({
  message: z
    .string()
    .trim()
    .min(1, "Message cannot be empty.")
    .max(
      env.maxMessageLength,
      `Message cannot exceed ${env.maxMessageLength} characters.`
    ),

  conversationId: z.string().optional(),

  language: z.enum(["en", "am"]).optional(),
});

export function validateChatRequest(
  req: Request,
  res: Response,
  next: NextFunction
) {
  const result = chatSchema.safeParse(req.body);

  if (!result.success) {
    res.status(400).json({
      error: "Invalid request.",
      details: result.error.flatten(),
    });

    return;
  }

  req.body = result.data;

  next();
}