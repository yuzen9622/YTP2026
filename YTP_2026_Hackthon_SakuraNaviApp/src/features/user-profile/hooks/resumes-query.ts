import type { QueryClient } from "@tanstack/react-query";

export const RESUMES_QUERY_KEY = ["resumes"] as const;

export function invalidateResumes(queryClient: QueryClient): Promise<void> {
  return queryClient.invalidateQueries({ queryKey: RESUMES_QUERY_KEY });
}
