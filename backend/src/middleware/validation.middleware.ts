import { NextFunction, Request, Response } from "express";
import { z } from "zod";
import { env } from "../config/env.js";

const imageSchema = z.object({
  fileName: z.string().min(1).max(255),
  mimeType: z.enum(["image/jpeg", "image/png", "image/webp"]),
  dataUrl: z
    .string()
    .max(7_100_000, "Image is too large.")
    .regex(
      /^data:image\/(jpeg|png|webp);base64,[A-Za-z0-9+/]+={0,2}$/,
      "Invalid image data URL."
    ),
});

const chatSchema = z
  .object({
    message: z
      .string()
      .trim()
      .max(
        env.maxMessageLength,
        `Message cannot exceed ${env.maxMessageLength} characters.`
      )
      .default(""),

    conversationId: z.string().optional(),

    language: z.enum(["en", "am"]).optional(),

    image: imageSchema.optional(),
  })
  .refine(
    (data) => data.message.length > 0 || Boolean(data.image),
    { message: "Enter a message or attach an image." }
  )
  .refine(
    (data) =>
      !data.image ||
      data.image.dataUrl.startsWith(
        `data:${data.image.mimeType};base64,`
      ),
    {
      message: "Image MIME type does not match its data.",
      path: ["image", "dataUrl"],
    }
  );

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