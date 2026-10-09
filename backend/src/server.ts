import app from "./app.js";
import { env } from "./config/env.js";

app.listen(env.port, () => {
  console.log(
    `Hospital AI Agent backend running on http://localhost:${env.port}`
  );

  console.log(
    `Health check: http://localhost:${env.port}/health`
  );
});