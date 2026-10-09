import express from "express";
import cors from "cors";
import helmet from "helmet";
import { env } from "./config/env";
import chatRoutes from "./routes/chat.routes";
const app = express();
app.use(helmet({
    crossOriginResourcePolicy: false,
}));
app.use(cors({
    origin: env.frontendUrl,
}));
app.use(express.json({ limit: "1mb" }));
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
export default app;
//# sourceMappingURL=app.js.map