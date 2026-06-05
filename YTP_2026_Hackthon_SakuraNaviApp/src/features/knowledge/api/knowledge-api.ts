import { apiClient } from "@/lib/api";
import type {
  KnowledgeCategoriesResponse,
  KnowledgeCategory,
  KnowledgeSearchResponse,
  SearchKnowledgeParams,
} from "../types/knowledge";

export async function getKnowledgeCategories(): Promise<KnowledgeCategoriesResponse> {
  return apiClient.get<KnowledgeCategoriesResponse>("/knowledge/categories");
}

export async function getKnowledgeCategory(
  category: string,
): Promise<KnowledgeCategory> {
  return apiClient.get<KnowledgeCategory>(
    `/knowledge/categories/${encodeURIComponent(category)}`,
  );
}

export async function searchKnowledge(
  params: SearchKnowledgeParams,
): Promise<KnowledgeSearchResponse> {
  const q = params.q.trim();

  return apiClient.post<KnowledgeSearchResponse>("/rag/search", {
    query: q,
    top_k: params.top_k ?? 5,
    category: params.category?.trim() || undefined,
  });
}
