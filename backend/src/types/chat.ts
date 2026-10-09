import { Language } from "./patient.js";

export interface ChatRequest {
  message: string;
  conversationId?: string;
  language?: Language;
}

export interface AuthenticatedPatient {
  patientId: string;
}

export interface ChatResponse {
  conversationId: string;
  message: string;
  language: Language;
  toolsUsed: string[];
  safetyFlag: boolean;
}

export interface ConversationMessage {
  role: "user" | "assistant";
  content: string;
  timestamp: string;
}

export interface ToolExecutionContext {
  patientId: string;
  conversationId: string;
}