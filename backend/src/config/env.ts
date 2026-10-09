import "dotenv/config";

function getNumber(
  value: string | undefined,
  fallback: number
): number {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

export const env = {
  port: getNumber(process.env.PORT, 5000),

  nodeEnv: process.env.NODE_ENV ?? "development",

  llmApiKey: process.env.LLM_API_KEY ?? "",

  llmModel:
    process.env.LLM_MODEL ?? "gemini-flash-lite-latest",

  llmFallbackModel:
    process.env.LLM_FALLBACK_MODEL ?? "gemini-flash-latest",

  frontendUrl:
    process.env.FRONTEND_URL ??
    "http://localhost:5173",

  maxMessageLength:
    getNumber(process.env.MAX_MESSAGE_LENGTH, 2000),

  rateLimitWindowMs:
    getNumber(process.env.RATE_LIMIT_WINDOW_MS, 60000),

  rateLimitMaxRequests:
    getNumber(process.env.RATE_LIMIT_MAX_REQUESTS, 30),
};