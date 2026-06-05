export const POLICY_CATEGORIES_QUERY_KEY = (
  accessMode: "private" | "public" = "private",
) => ["policy", "categories", accessMode] as const;

export const policyDocumentsQueryKey = (
  category: string,
  accessMode: "private" | "public" = "private",
) => ["policy", "documents", category, accessMode] as const;

export const policyDocumentQueryKey = (
  documentId: string,
  accessMode: "private" | "public" = "private",
) => ["policy", "document", documentId, accessMode] as const;
