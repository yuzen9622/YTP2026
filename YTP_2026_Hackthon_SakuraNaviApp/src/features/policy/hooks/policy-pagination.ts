import type { PolicyDocumentListResponse } from "../types/policy";

export function resolveNextPolicyDocumentsOffset(
  lastPage: PolicyDocumentListResponse,
  allPages: PolicyDocumentListResponse[],
): number | undefined {
  const loadedCount = allPages.reduce((sum, page) => sum + page.items.length, 0);

  if (loadedCount >= lastPage.total) {
    return undefined;
  }

  return loadedCount;
}
