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

export type CareCaseWorkflowStatus =
  | "registered"
  | "acknowledged"
  | "in_review"
  | "resolved";

export interface CareCaseStatusEntry {
  status: CareCaseWorkflowStatus;
  timestamp: string;
  note: string;
}

export interface CareCase {
  caseId: string;
  caseType: "emergency_concern" | "urgent_concern";
  status: CareCaseWorkflowStatus;
  reportedConcern: string;
  createdAt: string;
  updatedAt: string;
  dataSource: "synthetic_demo";
  dataNotice: string;
  statusHistory: CareCaseStatusEntry[];
}

export type EmergencyContactAvailability =
  | "not_configured"
  | "partially_configured"
  | "configured";

export interface EmergencyDoctor {
  id: string;
  name: string;
  specialty: string;
  profileType: "fictional_demo";
  availability: "not_provided";
}

export interface EmergencyDepartmentDirectory {
  dataType: "fictional_demo";
  facilityName: string;
  departmentName: string;
  floor: string;
  roomNumber: string;
  address: string;
  directions: string;
  doctors: EmergencyDoctor[];
}

export interface EmergencyResponse {
  active: boolean;
  contactAvailability: EmergencyContactAvailability;
  hospitalName: string | null;
  hospitalEmergencyPhone: string | null;
  ambulanceDispatchPhone: string | null;
  alternativeEmergencyPhone: string | null;
  hospitalAddress: string | null;
  emergencyDirections: string | null;
  directory: EmergencyDepartmentDirectory | null;
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
  careCase?: CareCase | null;
  emergency?: EmergencyResponse | null;
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
  careCase: CareCase | null;
  emergency: EmergencyResponse | null;
}
