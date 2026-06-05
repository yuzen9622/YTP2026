export interface SubsidyRecommendationsRequest {
  resume_id?: string | null;
  query?: string | null;
  limit?: number;
}

export interface SubsidyRecommendationItem {
  title: string;
  amount?: string | null;
  department?: string | null;
  document_id?: string | null;
  source_link?: string | null;
}

export interface SubsidyRecommendationsResponse {
  items: SubsidyRecommendationItem[];
}

export interface NewsItem {
  date?: string | null;
  title: string;
  summary: string;
  document_id?: string | null;
  source_link?: string | null;
}

export interface NewsResponse {
  items: NewsItem[];
}

export interface AnnouncementItem {
  title: string;
  summary: string;
  published_at?: string | null;
  document_id?: string | null;
  source_link?: string | null;
}

export interface AnnouncementsResponse {
  items: AnnouncementItem[];
}

export interface YouthSubsidyDocumentItem {
  id: string;
  filename: string;
  title: string;
  category: string;
  source_url?: string | null;
  doc_metadata?: Record<string, unknown> | null;
  content_hash: string;
  chunk_count: number;
  created_at: string;
  updated_at: string;
}

export interface YouthSubsidyDocumentsResponse {
  items: YouthSubsidyDocumentItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface HomeSubsidyRankingItem {
  id: string;
  title: string;
  amountText: string;
  departmentText: string;
  documentId?: string | null;
  sourceLink?: string | null;
}

export interface HomeSubsidyRankingViewModel {
  source: "resume" | "fallback";
  items: HomeSubsidyRankingItem[];
}

export interface HomeNewsItemViewModel {
  id: string;
  title: string;
  summary: string;
  dateText: string;
  monthText: string;
  dayText: string;
  weekText: string;
  isToday: boolean;
  documentId?: string | null;
  sourceLink?: string | null;
}

export interface HomeAnnouncementItemViewModel {
  id: string;
  title: string;
  summary: string;
  publishedAtText: string;
  documentId?: string | null;
  sourceLink?: string | null;
}
