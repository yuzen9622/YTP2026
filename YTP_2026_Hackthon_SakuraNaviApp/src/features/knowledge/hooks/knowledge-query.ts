export const KNOWLEDGE_CATEGORIES_QUERY_KEY = ["knowledge", "categories"] as const;

export const knowledgeCategoryQueryKey = (category: string) =>
  ["knowledge", "categories", category] as const;

export const knowledgeSearchQueryKey = (
  q: string,
  category?: string | null,
  top_k?: number,
) => ["knowledge", "search", q, category ?? null, top_k ?? null] as const;
