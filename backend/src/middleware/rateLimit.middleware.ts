import rateLimit from "express-rate-limit";
import { env } from "../config/env.js";

export const chatRateLimiter = rateLimit({
  windowMs: env.rateLimitWindowMs,
  limit: env.rateLimitMaxRequests,
  standardHeaders: "draft-8",
  legacyHeaders: false,
  message: {
    error:
      "Too many requests. Please wait before sending another message.",
  },
});