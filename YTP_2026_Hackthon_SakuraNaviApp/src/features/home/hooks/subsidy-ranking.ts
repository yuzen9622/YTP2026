import {
  listYouthSubsidyDocuments,
  recommendSubsidies,
} from "../api/home-api";
import type {
  HomeSubsidyRankingItem,
  HomeSubsidyRankingViewModel,
  YouthSubsidyDocumentItem,
} from "../types/home";

const DEFAULT_LIMIT = 5;
const SAFE_TEXT = "--";

function toSafeText(value?: string | null): string {
  const normalized = value?.trim();
  return normalized ? normalized : SAFE_TEXT;
}

function extractDocumentText(
  metadata: Record<string, unknown> | null | undefined,
  keys: string[],
): string | null {
  if (!metadata) {
    return null;
  }

  for (const key of keys) {
    const value = Reflect.get(metadata, key);
    if (typeof value === "string" && value.trim().length > 0) {
      return value.trim();
    }
  }

  return null;
}

function mapFallbackDocument(item: YouthSubsidyDocumentItem): HomeSubsidyRankingItem {
  const amount = extractDocumentText(item.doc_metadata, [
    "amount",
    "grant_amount",
    "subsidy_amount",
    "補助金額",
  ]);
  const department = extractDocumentText(item.doc_metadata, [
    "department",
    "organizer",
    "authority",
    "agency",
    "局處",
    "主辦單位",
  ]);

  return {
    id: item.id,
    title: item.title,
    amountText: toSafeText(amount),
    departmentText: toSafeText(department),
    documentId: item.id,
    sourceLink: item.source_url ?? null,
  };
}

interface FetchHomeSubsidyRankingParams {
  primaryResumeId?: string | null;
  query?: string | null;
  limit?: number;
  accessMode?: "private" | "public";
}

export async function fetchHomeSubsidyRanking(
  params: FetchHomeSubsidyRankingParams,
): Promise<HomeSubsidyRankingViewModel> {
  const limit = params.limit ?? DEFAULT_LIMIT;
  const primaryResumeId = params.primaryResumeId?.trim() || null;

  if (primaryResumeId) {
    const response = await recommendSubsidies({
      resume_id: primaryResumeId,
      query: params.query,
      limit,
    });

    return {
      source: "resume",
      items: response.items.map((item, index) => ({
        id: `resume-${index}-${item.title}`,
        title: item.title,
        amountText: toSafeText(item.amount),
        departmentText: toSafeText(item.department),
        documentId: item.document_id ?? null,
        sourceLink: item.source_link ?? null,
      })),
    };
  }

  const fallbackResponse = await listYouthSubsidyDocuments(limit, {
    accessMode: params.accessMode ?? "private",
  });
  return {
    source: "fallback",
    items: fallbackResponse.items.map(mapFallbackDocument),
  };
}
