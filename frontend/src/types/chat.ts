export type Language = "en" | "am";

export type SummaryDetail = "short" | "normal" | "detailed";

export type MessageRole = "user" | "assistant";

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: string;
  safety?: {
    requiresAttention: boolean;
  };
}

export interface ChatRequest {
  message: string;
  conversationId: string;
  language: Language;
  detail: SummaryDetail;
}

export interface ChatAction {
  label: string;
  type: "navigate" | "care_team_message";
  target?: string;
}

export interface ChatResponse {
  message: string;
  conversationId: string;
  language: Language;
  safety?: {
    requiresAttention: boolean;
    message?: string;
    offerCareTeamMessage?: boolean;
  };
  actions?: ChatAction[];
}