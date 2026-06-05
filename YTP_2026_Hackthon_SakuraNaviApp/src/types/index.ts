export interface User {
  id: string; // UUID，由 Backend 發派
  email: string | null; // 帳號 email
  name: string; // 顯示名稱

  account: string;
  phone: string | null;
  bio: string; // 自我介紹
  birth_date: string | null;
  avatar_url: string | null;
  language_skills: LanguageSkill[];
  is_active: boolean;
  created_at: string; // ISO 8601
  updated_at: string; // ISO 8601

  // Backward compatibility aliases
  createdAt?: string; // ISO 8601
  updatedAt?: string;
  age: number | null;
  tags: string[]; // e.g. ["人文社科", "設計", "資訊工程"]
  location?: string; // e.g. "台北市大安區"
  expectedSalary?: SalaryRange;
  career?: CareerStatus | null;
  gender?: Gender | null;
  registered_address?: string | null;
  residential_address?: string | null;
  is_residential_same_as_registered?: boolean;
  educationLevel?: EducationLevel;
}

export type SalaryRange = "under_30k" | "30k_40k" | "40k_60k" | "above_60k";

export type CareerStatus = "unemployed" | "employed" | "student";
export type Gender = "male" | "female" | "hidden";

export type CareerStage =
  | "student" // 在學
  | "job_seeking" // 待業
  | "switching" // 轉職
  | "entrepreneurship"; // 創業

export type EducationLevel =
  | "high_school"
  | "associate"
  | "bachelor"
  | "master"
  | "phd";

export type LanguageProficiency =
  | "native"
  | "advanced"
  | "upper_intermediate"
  | "intermediate"
  | "basic";

export interface LanguageSkill {
  language: string;
  proficiency: LanguageProficiency;
}

// ─── 最新政府資訊（v2 新增）──────────────────────────────────
export interface PolicyNews {
  id: string;
  title: string;
  summary: string; // ≤150 字
  category: PolicyCategory;
  publishedAt: string; // ISO 8601
  sourceUrl: string;
  imageUrl?: string;
  isNew: boolean; // 48 小時內發布
}

export type ConversationType = "career" | "startup" | "learning";

export type StreamPhase =
  | "idle"
  | "requesting"
  | "streaming"
  | "done"
  | "error";

// ─── 對話 / Chat ──────────────────────────────────────────────
export interface ChatMessage {
  messageId: string; // UUID
  id?: string;
  conversationId: string; // 同一對話 conversation 共享
  role: "user" | "assistant";
  content: string; // Markdown 格式
  recommendations?: PolicyCard[];
  sources?: PolicySource[]; // RAG 來源標注，assistant 訊息才有值
  timestamp: string; // ISO 8601
  status?: "pending" | "streaming" | "done" | "error";
}

export interface PolicySource {
  id: string;
  name: string;
  url?: string;
  publishedAt?: string;
  sourceId?: string;
  title?: string;
  snippet?: string; // 引用段落摘要（≤100字）
  relevanceScore?: number; // 0.0 ~ 1.0
}

// 後端 Conversation schema: id, title, created_at, updated_at
// 前端擴展欄位（optional，保持向後相容）
export interface Conversation {
  id: string;
  title: string;
  createdAt: string;
  updatedAt: string;
  // 前端擴展
  pinned?: boolean;
  lastMessageAt?: string;
  unread?: number;
  status?: "active" | "awaiting" | "resolved";
  topic?: string;
  caseId?: string;
  messages?: ChatMessage[];
}

export type ChatConversation = Conversation;

// ─── 服務路徑 ─────────────────────────────────────────────────
export interface ServicePath {
  pathId: string;
  userId: string;
  steps: ServiceStep[];
  currentStepIndex: number;
  generatedAt: string;
}

export interface ServiceStep {
  stepId: string;
  order: number;
  title: string; // e.g. "職涯心理測驗"
  description: string;
  policyId: string; // 對應政策 ID
  actionUrl: string; // 外部申辦連結
  status: "pending" | "in_progress" | "completed";
}

// ─── 政策卡片 ─────────────────────────────────────────────────
export interface PolicyCard {
  policyId: string;
  id?: string;
  title: string;
  reason: string;
  saved?: boolean;
  category: PolicyCategory;
  summary: string; // ≤200字摘要
  tags: string[];
  deadline: string | null; // ISO 8601 or null
  applyUrl: string;
  sourceDocUrl: string;
}

export interface UserProfileSnapshot {
  city?: string;
  education?: string;
  careerStage?: string;
  interests?: string[];
}

export interface UserProfile {
  userId: string;
  age: number;
  fieldTags: string[];
  location: string;
  expectedSalary: SalaryRange;
  careerStage: CareerStage;
  educationLevel: EducationLevel;
  createdAt: string;
  updatedAt: string;
}

export type PolicyCategory =
  | "internship" // 實習
  | "subsidy" // 補助
  | "training" // 培訓
  | "loan" // 創業貸款
  | "counseling"; // 諮詢輔導
