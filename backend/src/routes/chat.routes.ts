import { Router } from "express";
import { chatController } from "../controllers/chat.controller.js";
import { authenticatePatient } from "../middleware/auth.middleware.js";
import { chatRateLimiter } from "../middleware/rateLimit.middleware.js";
import { validateChatRequest } from "../middleware/validation.middleware.js";

const router = Router();

router.post(
  "/",
  authenticatePatient,
  chatRateLimiter,
  validateChatRequest,
  chatController
);

export default router;