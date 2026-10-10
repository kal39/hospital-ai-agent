
export type Language = "en" | "am";

export type SummaryDetail = "short" | "normal" | "detailed";

export type MessageRole = "user" | "assistant";


export interface ChatImage {
  fileName: string;
  mimeType: "image/jpeg" | "image/png" | "image/webp" | "application/pdf";
  dataUrl: string;
}

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: string;
  attachment?: ChatImage;
  safety?: {
    requiresAttention: boolean;
  };
}

export interface ChatRequest {
  message: string;
  conversationId: string;
  language: Language;
  detail: SummaryDetail;
  image?: ChatImage;
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