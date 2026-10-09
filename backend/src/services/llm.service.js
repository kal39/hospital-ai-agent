import { env } from "../config/env";
export class LLMService {
    async generate(messages) {
        if (!env.llmApiKey) {
            return this.fallbackResponse(messages);
        }
        const input = messages
            .filter((message) => message.role !== "system")
            .map((message) => ({
            role: message.role,
            content: message.content,
        }));
        const instructions = messages.find((message) => message.role === "system")
            ?.content ?? "";
        const response = await fetch(env.llmApiUrl, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                Authorization: `Bearer ${env.llmApiKey}`,
            },
            body: JSON.stringify({
                model: env.llmModel,
                instructions,
                input,
                max_output_tokens: 700,
            }),
        });
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`LLM request failed: ${response.status} ${errorText}`);
        }
        const data = (await response.json());
        if (!data.output_text) {
            throw new Error("LLM returned no text.");
        }
        return data.output_text;
    }
    fallbackResponse(messages) {
        const userMessage = messages.find((message) => message.role === "user")?.content ?? "";
        return `I received your request: "${userMessage}". The LLM API is not configured yet, so I cannot generate the full AI explanation. The hospital data and agent tools are working, and the LLM can be enabled by adding LLM_API_KEY to backend/.env.`;
    }
}
export const llmService = new LLMService();
//# sourceMappingURL=llm.service.js.map