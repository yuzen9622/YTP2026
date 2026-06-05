import { useQuery, type UseQueryResult } from "@tanstack/react-query";
import {
  getKnowledgeCategories,
  getKnowledgeCategory,
  searchKnowledge,
} from "../api/knowledge-api";
import {
  KNOWLEDGE_CATEGORIES_QUERY_KEY,
  knowledgeCategoryQueryKey,
  knowledgeSearchQueryKey,
} from "./knowledge-query";
import type {
  KnowledgeCategoriesResponse,
  KnowledgeCategory,
  KnowledgeSearchResponse,
} from "../types/knowledge";

export function useKnowledgeCategoriesQuery(): UseQueryResult<
  KnowledgeCategoriesResponse,
  Error
> {
  return useQuery<KnowledgeCategoriesResponse, Error>({
    queryKey: KNOWLEDGE_CATEGORIES_QUERY_KEY,
    queryFn: getKnowledgeCategories,
  });
}

export function useKnowledgeCategoryQuery(
  category: string,
): UseQueryResult<KnowledgeCategory, Error> {
  return useQuery<KnowledgeCategory, Error>({
    queryKey: knowledgeCategoryQueryKey(category),
    queryFn: () => getKnowledgeCategory(category),
    enabled: category.trim().length > 0,
  });
}

export function useKnowledgeSearchQuery(
  q: string,
  options?: { category?: string | null; top_k?: number },
): UseQueryResult<KnowledgeSearchResponse, Error> {
  const normalizedQ = q.trim();
  const normalizedCategory = options?.category?.trim() || undefined;
  const normalizedTopK = options?.top_k;

  return useQuery<KnowledgeSearchResponse, Error>({
    queryKey: knowledgeSearchQueryKey(
      normalizedQ,
      normalizedCategory,
      normalizedTopK,
    ),
    queryFn: () =>
      searchKnowledge({
        q: normalizedQ,
        category: normalizedCategory,
        top_k: normalizedTopK,
      }),
    enabled: normalizedQ.length > 0,
  });
}
