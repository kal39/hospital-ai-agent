import app from "./app";
import { env } from "./config/env";
app.listen(env.port, () => {
    console.log(`Hospital AI Agent backend running on http://localhost:${env.port}`);
    console.log(`Health check: http://localhost:${env.port}/health`);
});
//# sourceMappingURL=server.js.map