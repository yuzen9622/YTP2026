import { apiClient, resolveWithAuth, type ApiAccessOptions } from "@/lib/api";
import type {
  ListPolicyDocumentsParams,
  PolicyCategoryListResponse,
  PolicyDocumentListResponse,
  PolicyDocumentResponse,
} from "../types/policy";

const DEFAULT_DOCUMENTS_LIMIT = 20;

export async function getPolicyCategories(
  options?: ApiAccessOptions,
): Promise<PolicyCategoryListResponse> {
  return apiClient.get<PolicyCategoryListResponse>("/rag/categories", {
    withAuth: resolveWithAuth(options),
  });
}

export async function getPolicyDocuments(
  params: ListPolicyDocumentsParams,
  options?: ApiAccessOptions,
): Promise<PolicyDocumentListResponse> {
  const normalizedCategory = params.category?.trim() || undefined;

  return apiClient.get<PolicyDocumentListResponse>("/rag/documents", {
    params: {
      category: normalizedCategory,
      limit: params.limit ?? DEFAULT_DOCUMENTS_LIMIT,
      offset: params.offset ?? 0,
    },
    withAuth: resolveWithAuth(options),
  });
}

export async function getPolicyDocument(
  documentId: string,
  options?: {
    include_chunks?: boolean;
    include_raw_content?: boolean;
  },
  accessOptions?: ApiAccessOptions,
): Promise<PolicyDocumentResponse> {
  return apiClient.get<PolicyDocumentResponse>(
    `/rag/documents/${encodeURIComponent(documentId)}`,
    {
      params: {
        include_chunks: options?.include_chunks ?? true,
        include_raw_content: options?.include_raw_content ?? true,
      },
      withAuth: resolveWithAuth(accessOptions),
    },
  );
}
