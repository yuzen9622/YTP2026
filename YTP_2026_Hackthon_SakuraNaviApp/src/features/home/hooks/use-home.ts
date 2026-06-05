import { useMemo } from "react";
import { useQuery, type UseQueryResult } from "@tanstack/react-query";
import { useResumesQuery } from "@/features/user-profile/hooks/use-resumes";
import {
  listHomeAnnouncements,
  listHomeNews,
} from "../api/home-api";
import {
  homeAnnouncementsQueryKey,
  homeNewsQueryKey,
  homeSubsidyRankingQueryKey,
} from "./home-query";
import type {
  HomeAnnouncementItemViewModel,
  HomeNewsItemViewModel,
  HomeSubsidyRankingViewModel,
} from "../types/home";
import { buildHomeDateParts, formatHomeDate } from "../utils/home-format";
import { fetchHomeSubsidyRanking } from "./subsidy-ranking";

const DEFAULT_LIMIT = 5;

interface UseHomeListOptions {
  query?: string | null;
  limit?: number;
  accessMode?: "private" | "public";
}

export function useHomeSubsidyRankingQuery(
  options?: UseHomeListOptions,
): UseQueryResult<HomeSubsidyRankingViewModel, Error> {
  const accessMode = options?.accessMode ?? "private";
  const usePrivateResume = accessMode === "private";
  const resumesQuery = useResumesQuery({ enabled: usePrivateResume });

  const primaryResumeId = useMemo(() => {
    if (!usePrivateResume) {
      return null;
    }
    return (
      resumesQuery.data?.find((resume) => resume.is_primary)?.id?.trim() || null
    );
  }, [resumesQuery.data, usePrivateResume]);

  const normalizedQuery = options?.query?.trim() || undefined;
  const limit = options?.limit ?? DEFAULT_LIMIT;

  return useQuery<HomeSubsidyRankingViewModel, Error>({
    queryKey: homeSubsidyRankingQueryKey(
      primaryResumeId,
      normalizedQuery,
      limit,
      accessMode,
    ),
    queryFn: () =>
      fetchHomeSubsidyRanking({
        primaryResumeId,
        query: normalizedQuery,
        limit,
        accessMode,
      }),
    enabled: usePrivateResume ? !resumesQuery.isLoading : true,
  });
}

export function useHomeNewsQuery(
  options?: UseHomeListOptions,
): UseQueryResult<HomeNewsItemViewModel[], Error> {
  const accessMode = options?.accessMode ?? "private";
  const normalizedQuery = options?.query?.trim() || undefined;
  const limit = options?.limit ?? DEFAULT_LIMIT;

  return useQuery({
    queryKey: homeNewsQueryKey(normalizedQuery, limit, accessMode),
    queryFn: () =>
      listHomeNews(
        { query: normalizedQuery, limit },
        {
          accessMode,
        },
      ),
    select: (response): HomeNewsItemViewModel[] => {
      return response.items.map((item, index) => {
        const dateParts = buildHomeDateParts(item.date);

        return {
          id: `news-${index}-${item.title}`,
          title: item.title,
          summary: item.summary,
          dateText: dateParts.dateText,
          monthText: dateParts.monthText,
          dayText: dateParts.dayText,
          weekText: dateParts.weekText,
          isToday: dateParts.isToday,
          documentId: item.document_id ?? null,
          sourceLink: item.source_link ?? null,
        };
      });
    },
  });
}

export function useHomeAnnouncementsQuery(
  options?: UseHomeListOptions,
): UseQueryResult<HomeAnnouncementItemViewModel[], Error> {
  const accessMode = options?.accessMode ?? "private";
  const normalizedQuery = options?.query?.trim() || undefined;
  const limit = options?.limit ?? DEFAULT_LIMIT;

  return useQuery({
    queryKey: homeAnnouncementsQueryKey(normalizedQuery, limit, accessMode),
    queryFn: () =>
      listHomeAnnouncements(
        { query: normalizedQuery, limit },
        {
          accessMode,
        },
      ),
    select: (response): HomeAnnouncementItemViewModel[] => {
      return response.items.map((item, index) => ({
        id: `announcement-${index}-${item.title}`,
        title: item.title,
        summary: item.summary,
        publishedAtText: formatHomeDate(item.published_at),
        documentId: item.document_id ?? null,
        sourceLink: item.source_link ?? null,
      }));
    },
  });
}
