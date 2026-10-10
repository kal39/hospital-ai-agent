
import express from "express";
import cors from "cors";
import helmet from "helmet";

import { env } from "./config/env.js";
import chatRoutes from "./routes/chat.routes.js";

const app = express();

app.use(
  helmet({
    crossOriginResourcePolicy: false,
  })
);

app.use(
  cors({
    origin: env.frontendUrl,
  })
);

// A 5 MB binary file expands to about 6.67 MB in Base64.
// Leave room for JSON fields while keeping an explicit request limit.
app.use(express.json({ limit: "8mb" }));

app.get("/health", (_req, res) => {
  res.json({
    status: "ok",
    service: "hospital-ai-agent",
    environment: env.nodeEnv,
  });
});

app.use("/api/chat", chatRoutes);

app.use((_req, res) => {
  res.status(404).json({
    error: "Route not found.",
  });
});

// Convert oversized JSON requests into a clear client error.
app.use(
  (
    error: unknown,
    _req: express.Request,
    res: express.Response,
    next: express.NextFunction
  ) => {
    if (
      typeof error === "object" &&
      error !== null &&
      "type" in error &&
      error.type === "entity.too.large"
    ) {
      res.status(413).json({
        error: "The request is too large. Upload a file no larger than 5 MB.",
      });
      return;
    }

    next(error);
  }
);

export default app;
