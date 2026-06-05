import { getApiBaseUrl } from "@/lib/api";

export interface SitemapPolicyDocumentItem {
  id: string;
  updated_at: string | null;
}

interface PolicyDocumentListResponse {
  items: SitemapPolicyDocumentItem[];
  total: number;
  limit: number;
  offset: number;
}

const MAX_SITEMAP_DOCUMENTS = 200;
const PAGE_SIZE = 50;

function buildDocumentsUrl(limit: number, offset: number): string {
  const base = getApiBaseUrl().replace(/\/+$/, "");
  return `${base}/rag/documents?limit=${limit}&offset=${offset}`;
}

export async function fetchSitemapPolicyDocuments(): Promise<SitemapPolicyDocumentItem[]> {
  const documents: SitemapPolicyDocumentItem[] = [];
  let offset = 0;

  while (documents.length < MAX_SITEMAP_DOCUMENTS) {
    const limit = Math.min(PAGE_SIZE, MAX_SITEMAP_DOCUMENTS - documents.length);
    const response = await fetch(buildDocumentsUrl(limit, offset), {
      method: "GET",
      headers: {
        Accept: "application/json",
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to load policy documents for sitemap: ${response.status}`);
    }

    const payload = (await response.json()) as PolicyDocumentListResponse;
    const items = payload.items ?? [];

    if (items.length === 0) {
      break;
    }

    documents.push(...items);

    if (items.length < limit) {
      break;
    }

    offset += limit;
  }

  return documents.slice(0, MAX_SITEMAP_DOCUMENTS);
}
