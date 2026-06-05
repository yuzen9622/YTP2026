import { apiClient, resolveWithAuth, type ApiAccessOptions } from "@/lib/api";
import type {
  AnnouncementsResponse,
  NewsResponse,
  SubsidyRecommendationsRequest,
  SubsidyRecommendationsResponse,
  YouthSubsidyDocumentsResponse,
} from "../types/home";

const DEFAULT_LIMIT = 5;
const YOUTH_SUBSIDY_CATEGORY = "youth_subsidy";

interface ListParams {
  query?: string | null;
  limit?: number;
}

function normalizeQuery(value?: string | null): string | undefined {
  const normalized = value?.trim();
  return normalized ? normalized : undefined;
}

export async function recommendSubsidies(
  payload: SubsidyRecommendationsRequest,
  options?: ApiAccessOptions,
): Promise<SubsidyRecommendationsResponse> {
  return apiClient.post<SubsidyRecommendationsResponse>(
    "/rag/recommendations/subsidies",
    {
      resume_id: payload.resume_id?.trim() || undefined,
      query: normalizeQuery(payload.query),
      limit: payload.limit ?? DEFAULT_LIMIT,
    },
    {
      withAuth: resolveWithAuth(options),
    },
  );
}

export async function listHomeNews(
  params?: ListParams,
  options?: ApiAccessOptions,
): Promise<NewsResponse> {
  return apiClient.get<NewsResponse>("/rag/news", {
    params: {
      query: normalizeQuery(params?.query),
      limit: params?.limit ?? DEFAULT_LIMIT,
    },
    withAuth: resolveWithAuth(options),
  });
}

export async function listHomeAnnouncements(
  params?: ListParams,
  options?: ApiAccessOptions,
): Promise<AnnouncementsResponse> {
  return apiClient.get<AnnouncementsResponse>("/rag/announcements", {
    params: {
      query: normalizeQuery(params?.query),
      limit: params?.limit ?? DEFAULT_LIMIT,
    },
    withAuth: resolveWithAuth(options),
  });
}

export async function listYouthSubsidyDocuments(
  limit = DEFAULT_LIMIT,
  options?: ApiAccessOptions,
): Promise<YouthSubsidyDocumentsResponse> {
  return apiClient.get<YouthSubsidyDocumentsResponse>("/rag/documents", {
    params: {
      category: YOUTH_SUBSIDY_CATEGORY,
      limit,
      offset: 0,
    },
    withAuth: resolveWithAuth(options),
  });
}
