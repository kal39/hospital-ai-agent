interface LLMMessage {
    role: "system" | "user" | "assistant";
    content: string;
}
export declare class LLMService {
    generate(messages: LLMMessage[]): Promise<string>;
    private fallbackResponse;
}
export declare const llmService: LLMService;
export {};
//# sourceMappingURL=llm.service.d.ts.map