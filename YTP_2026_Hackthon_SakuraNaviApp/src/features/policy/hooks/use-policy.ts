import {
  useInfiniteQuery,
  useQuery,
  type InfiniteData,
  type UseInfiniteQueryResult,
  type UseQueryResult,
} from "@tanstack/react-query";
import {
  getPolicyCategories,
  getPolicyDocument,
  getPolicyDocuments,
} from "../api/policy-api";
import {
  POLICY_CATEGORIES_QUERY_KEY,
  policyDocumentQueryKey,
  policyDocumentsQueryKey,
} from "./policy-query";
import { resolveNextPolicyDocumentsOffset } from "./policy-pagination";
import type {
  PolicyCategoryListResponse,
  PolicyDocumentListResponse,
  PolicyDocumentResponse,
} from "../types/policy";

export const POLICY_DOCUMENTS_PAGE_SIZE = 20;

interface PolicyQueryOptions {
  accessMode?: "private" | "public";
}

export function usePolicyCategoriesQuery(
  options?: PolicyQueryOptions,
): UseQueryResult<
  PolicyCategoryListResponse,
  Error
> {
  const accessMode = options?.accessMode ?? "private";

  return useQuery<PolicyCategoryListResponse, Error>({
    queryKey: POLICY_CATEGORIES_QUERY_KEY(accessMode),
    queryFn: () => getPolicyCategories({ accessMode }),
  });
}

export function usePolicyDocumentsInfiniteQuery(
  category: string,
  options?: {
    limit?: number;
  } & PolicyQueryOptions,
): UseInfiniteQueryResult<
  InfiniteData<PolicyDocumentListResponse, number>,
  Error
> {
  const normalizedCategory = category.trim();
  const limit = options?.limit ?? POLICY_DOCUMENTS_PAGE_SIZE;
  const accessMode = options?.accessMode ?? "private";

  return useInfiniteQuery<
    PolicyDocumentListResponse,
    Error,
    InfiniteData<PolicyDocumentListResponse, number>,
    ReturnType<typeof policyDocumentsQueryKey>,
    number
  >({
    queryKey: policyDocumentsQueryKey(normalizedCategory, accessMode),
    queryFn: ({ pageParam }) =>
      getPolicyDocuments({
        category: normalizedCategory,
        limit,
        offset: pageParam,
      }, { accessMode }),
    initialPageParam: 0,
    getNextPageParam: (lastPage, allPages) =>
      resolveNextPolicyDocumentsOffset(lastPage, allPages),
    enabled: normalizedCategory.length > 0,
  });
}

export function usePolicyDocumentQuery(
  documentId: string,
  options?: PolicyQueryOptions,
): UseQueryResult<PolicyDocumentResponse, Error> {
  const normalizedDocumentId = documentId.trim();
  const accessMode = options?.accessMode ?? "private";

  return useQuery<PolicyDocumentResponse, Error>({
    queryKey: policyDocumentQueryKey(normalizedDocumentId, accessMode),
    queryFn: () =>
      getPolicyDocument(normalizedDocumentId, {
        include_chunks: true,
        include_raw_content: true,
      }, { accessMode }),
    enabled: normalizedDocumentId.length > 0,
  });
}
