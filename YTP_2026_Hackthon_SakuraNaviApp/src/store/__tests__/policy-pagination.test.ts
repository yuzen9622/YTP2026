import { resolveNextPolicyDocumentsOffset } from "@/features/policy/hooks/policy-pagination";
import type {
  PolicyDocumentListResponse,
  PolicyDocumentResponse,
} from "@/features/policy/types/policy";

function createDocument(id: string): PolicyDocumentResponse {
  return {
    id,
    filename: `${id}.md`,
    title: `文件 ${id}`,
    category: "general",
    source_url: null,
    doc_metadata: null,
    content_hash: `hash-${id}`,
    chunk_count: 0,
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
    raw_content: null,
    chunks: [],
  };
}

function createPage(params: {
  itemCount: number;
  total: number;
  offset: number;
  limit: number;
}): PolicyDocumentListResponse {
  return {
    items: Array.from({ length: params.itemCount }, (_, index) => {
      return createDocument(`doc-${params.offset + index}`);
    }),
    total: params.total,
    limit: params.limit,
    offset: params.offset,
  };
}

describe("resolveNextPolicyDocumentsOffset", () => {
  it("returns next offset when there are still documents to fetch", () => {
    const pages = [
      createPage({ itemCount: 20, total: 55, offset: 0, limit: 20 }),
      createPage({ itemCount: 20, total: 55, offset: 20, limit: 20 }),
    ];

    const nextOffset = resolveNextPolicyDocumentsOffset(pages[1], pages);

    expect(nextOffset).toBe(40);
  });

  it("returns undefined when already loaded all documents", () => {
    const pages = [
      createPage({ itemCount: 20, total: 40, offset: 0, limit: 20 }),
      createPage({ itemCount: 20, total: 40, offset: 20, limit: 20 }),
    ];

    const nextOffset = resolveNextPolicyDocumentsOffset(pages[1], pages);

    expect(nextOffset).toBeUndefined();
  });

  it("returns undefined when final page is partial and reaches total", () => {
    const pages = [
      createPage({ itemCount: 20, total: 35, offset: 0, limit: 20 }),
      createPage({ itemCount: 15, total: 35, offset: 20, limit: 20 }),
    ];

    const nextOffset = resolveNextPolicyDocumentsOffset(pages[1], pages);

    expect(nextOffset).toBeUndefined();
  });
});
