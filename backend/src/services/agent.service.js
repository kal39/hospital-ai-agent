import { getPatientProfile } from "../tools/getPatientProfile";
import { getLatestLabResults } from "../tools/getLatestLabResults";
import { getMedications } from "../tools/getMedications";
import { getMedicalHistory } from "../tools/getMedicalHistory";
import { compareLabResults } from "../tools/compareLabResults";
import { getGlossaryContext } from "../glossary/medicalTerms";
import { llmService } from "./llm.service";
import { evaluateSafety } from "./safety.service";
import { recordAuditEvent } from "./audit.service";
import { ConversationMessage, ToolExecutionContext, } from "../types/chat";
const conversations = new Map();
export class AgentService {
    async run(userMessage, context, language) {
        const safety = evaluateSafety(userMessage);
        if (safety.blocked) {
            recordAuditEvent({
                patientId: context.patientId,
                conversationId: context.conversationId,
                event: "SAFETY_BLOCK",
                details: {
                    urgent: safety.urgent,
                },
            });
            return {
                message: safety.message,
                toolsUsed: [],
                safetyFlag: true,
            };
        }
        const history = conversations.get(context.conversationId) ?? [];
        const toolsUsed = [];
        /*
         * This is our first deterministic agent router.
         *
         * As the project grows, this router can be replaced with
         * model-driven structured tool calling without changing
         * the hospital tool implementations.
         */
        let toolData = null;
        let intent = "general";
        if (/lab|blood test|result|glucose|hemoglobin|creatinine/i.test(userMessage)) {
            intent = "lab_results";
            toolData = getLatestLabResults(context.patientId);
            toolsUsed.push("getLatestLabResults");
        }
        if (/compare|trend|previous result|changed|change/i.test(userMessage) &&
            /lab|result|blood|glucose|hemoglobin|creatinine/i.test(userMessage)) {
            intent = "lab_comparison";
            toolData = compareLabResults(context.patientId);
            toolsUsed.push("compareLabResults");
        }
        if (/medication|medicine|drug|tablet|dose|schedule/i.test(userMessage)) {
            intent = "medications";
            toolData = getMedications(context.patientId);
            toolsUsed.push("getMedications");
        }
        if (/history|previous visit|past treatment|medical history/i.test(userMessage)) {
            intent = "history";
            toolData = getMedicalHistory(context.patientId);
            toolsUsed.push("getMedicalHistory");
        }
        if (/profile|my information|my details|allerg/i.test(userMessage)) {
            intent = "profile";
            toolData = getPatientProfile(context.patientId);
            toolsUsed.push("getPatientProfile");
        }
        const systemPrompt = `
You are a hospital patient information assistant.

You are NOT a doctor and must not diagnose diseases, prescribe treatment,
or independently tell patients to start, stop, increase, or decrease medication.

The hospital's records are the source of truth.

You may explain information retrieved from authorized hospital tools.

If the provided data does not contain the answer, say that you do not have
enough information rather than inventing a medical fact.

Always distinguish:
1. What the patient's record says.
2. What the information generally means.
3. What requires discussion with a clinician.

Do not invent laboratory values, diagnoses, medication instructions,
appointments, or medical history.

For abnormal results, explain that an abnormal value does not automatically
mean a diagnosis and recommend discussing the result with the care team
when appropriate.

Language: ${language === "am" ? "Amharic" : "English"}.

For Amharic medical terminology, use the approved terminology glossary
below rather than inventing medical translations.

Approved glossary:
${getGlossaryContext()}
`;
        const conversationHistory = [
            ...history.slice(-8).map((item) => ({
                role: item.role,
                content: item.content,
            })),
        ];
        const userContext = `
Patient ID: ${context.patientId}

Detected intent: ${intent}

Authorized hospital data:
${JSON.stringify(toolData, null, 2)}

Patient request:
${userMessage}
`;
        const answer = await llmService.generate([
            {
                role: "system",
                content: systemPrompt,
            },
            ...conversationHistory,
            {
                role: "user",
                content: userContext,
            },
        ]);
        history.push({
            role: "user",
            content: userMessage,
            timestamp: new Date().toISOString(),
        });
        history.push({
            role: "assistant",
            content: answer,
            timestamp: new Date().toISOString(),
        });
        conversations.set(context.conversationId, history.slice(-20));
        recordAuditEvent({
            patientId: context.patientId,
            conversationId: context.conversationId,
            event: "AGENT_EXECUTION",
            details: {
                intent,
                toolsUsed,
            },
        });
        return {
            message: answer,
            toolsUsed,
            safetyFlag: false,
        };
    }
}
export const agentService = new AgentService();
//# sourceMappingURL=agent.service.js.map