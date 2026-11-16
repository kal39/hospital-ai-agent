export type Language = "en" | "am";

export type SummaryDetail = "short" | "normal" | "detailed";

export type MessageRole = "user" | "assistant";

export interface ChatImage {
  fileName: string;
  mimeType: "image/jpeg" | "image/png" | "image/webp" | "application/pdf";
  dataUrl: string;
}

export interface DoctorRecommendation {
  id: string;
  name: string;
  department: string;
  specialties: string[];
  location: string;
  isAssignedDoctor: boolean;
  dataSource: string;
  dataNotice: string;
}

export interface AppointmentSlotOption {
  doctorId: string;
  doctorName: string;
  department: string;
  location: string;
  date: string;
  time: string;
  slotRemainingCapacity: number;
  dailyRemainingCapacity: number;
  dataSource: string;
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
  doctorRecommendations?: DoctorRecommendation[];
  appointmentSlots?: AppointmentSlotOption[];
}

export interface ChatRequest {
  message: string;
  conversationId: string;
  language: Language;
  detail: SummaryDetail;
  image?: ChatImage;
}

export interface ChatResponse {
  message: string;
  conversationId: string;
  language: Language;
  detail: SummaryDetail;
  toolsUsed: string[];
  safetyFlag: boolean;
  safety: {
    requiresAttention: boolean;
  };
  doctorRecommendations: DoctorRecommendation[];
  appointmentSlots: AppointmentSlotOption[];
}
