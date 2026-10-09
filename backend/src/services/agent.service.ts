import { getPatientProfile } from "../tools/getPatientProfile.js";
import { getLatestLabResults } from "../tools/getLatestLabResults.js";
import { getMedications } from "../tools/getMedications.js";
import { getMedicalHistory } from "../tools/getMedicalHistory.js";
import { compareLabResults } from "../tools/compareLabResults.js";
import { getGlossaryContext } from "../glossary/medicalTerms.js";
import { llmService } from "./llm.service.js";
import { evaluateSafety } from "./safety.service.js";
import { recordAuditEvent } from "./audit.service.js";
import {
  ConversationMessage,
  ToolExecutionContext,
} from "../types/chat.js";

interface AgentResult {
  message: string;
  toolsUsed: string[];
  safetyFlag: boolean;
}

const conversations = new Map<string, ConversationMessage[]>();

export class AgentService {
  async run(
    userMessage: string,
    context: ToolExecutionContext,
    language: "en" | "am"
  ): Promise<AgentResult> {
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
        message: safety.message!,
        toolsUsed: [],
        safetyFlag: true,
      };
    }

    const history =
      conversations.get(context.conversationId) ?? [];

    const systemPrompt = `
You are a hospital patient information assistant.

You are NOT a doctor.

Your responsibilities:
- Help patients understand information contained in their authorized hospital records.
- Use hospital tools whenever the patient's question requires patient-specific information.
- Never invent patient information.
- Never invent laboratory values, diagnoses, medications, appointments, treatments, allergies, or history.
- The hospital record is the source of truth.

You may:
- Explain laboratory results.
- Compare laboratory results.
- Explain medication information already present in the hospital record.
- Summarize medical history.
- Explain permitted patient profile information.
- Explain medical terminology in simple language.

You must NOT:
- Diagnose diseases.
- Prescribe medication.
- Tell the patient to start, stop, increase, or decrease medication.
- Make treatment decisions.
- Claim that an abnormal laboratory result automatically means a diagnosis.
- Pretend to have access to information that was not returned by a hospital tool.

IMPORTANT TOOL RULE:
If the user asks about their own medical information, use the appropriate hospital tool instead of guessing.

Examples:
- Latest/current/recent laboratory results -> getLatestLabResults
- Compare/trend/change in laboratory results -> compareLabResults
- Current medications/medicines -> getMedications
- Medical history/past visits/treatments -> getMedicalHistory
- Patient information/profile/allergies -> getPatientProfile

The patient identity is already authenticated by the backend.
Never ask the user for a patient ID.

For abnormal laboratory results:
- Explain what the recorded result says.
- Explain the general meaning carefully.
- State that an abnormal result does not automatically establish a diagnosis.
- Recommend discussing clinically important findings with the care team.

Language:
Respond in ${language === "am" ? "Amharic" : "English"}.

For Amharic medical terminology:
Use the approved hospital terminology glossary below.

Approved terminology glossary:
${getGlossaryContext()}
`;

    const conversationHistory = history
      .slice(-8)
      .map((item) => ({
        role: item.role,
        content: item.content,
      }));

    const result = await llmService.generateWithTools({
      systemInstruction: systemPrompt,
      userMessage,
      conversationHistory,
      patientId: context.patientId,
    });

    const toolsUsed = result.toolsUsed;

    history.push({
      role: "user",
      content: userMessage,
      timestamp: new Date().toISOString(),
    });

    history.push({
      role: "assistant",
      content: result.message,
      timestamp: new Date().toISOString(),
    });

    conversations.set(
      context.conversationId,
      history.slice(-20)
    );

    recordAuditEvent({
      patientId: context.patientId,
      conversationId: context.conversationId,
      event: "AGENT_EXECUTION",
      details: {
        toolsUsed,
      },
    });

    return {
      message: result.message,
      toolsUsed,
      safetyFlag: false,
    };
  }
}

export const agentService = new AgentService();