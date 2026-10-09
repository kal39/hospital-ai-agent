import { Router } from "express";
import { chatController } from "../controllers/chat.controller";
import { authenticatePatient } from "../middleware/auth.middleware";
import { chatRateLimiter } from "../middleware/rateLimit.middleware";
import { validateChatRequest } from "../middleware/validation.middleware";
const router = Router();
router.post("/", authenticatePatient, chatRateLimiter, validateChatRequest, chatController);
export default router;
//# sourceMappingURL=chat.routes.js.map