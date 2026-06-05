export const homeSubsidyRankingQueryKey = (
  primaryResumeId: string | null,
  query?: string | null,
  limit?: number,
  accessMode?: "private" | "public",
) =>
  [
    "home",
    "subsidy-ranking",
    primaryResumeId,
    query ?? null,
    limit ?? null,
    accessMode ?? "private",
  ] as const;

export const homeNewsQueryKey = (
  query?: string | null,
  limit?: number,
  accessMode?: "private" | "public",
) => ["home", "news", query ?? null, limit ?? null, accessMode ?? "private"] as const;

export const homeAnnouncementsQueryKey = (
  query?: string | null,
  limit?: number,
  accessMode?: "private" | "public",
) =>
  ["home", "announcements", query ?? null, limit ?? null, accessMode ?? "private"] as const;
