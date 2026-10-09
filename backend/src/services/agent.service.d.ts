import { ToolExecutionContext } from "../types/chat.js";
interface AgentResult {
    message: string;
    toolsUsed: string[];
    safetyFlag: boolean;
}
export declare class AgentService {
    run(userMessage: string, context: ToolExecutionContext, language: "en" | "am"): Promise<AgentResult>;
}
export declare const agentService: AgentService;
export {};
//# sourceMappingURL=agent.service.d.ts.map