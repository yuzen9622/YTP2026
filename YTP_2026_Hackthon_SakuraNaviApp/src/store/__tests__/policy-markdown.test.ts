import {
  buildPolicyMarkdownContent,
  POLICY_MARKDOWN_EMPTY_CONTENT,
} from "@/features/policy/utils/policy-markdown";
import type { PolicyDocumentResponse } from "@/features/policy/types/policy";

function createDocument(
  overrides: Partial<PolicyDocumentResponse> = {},
): PolicyDocumentResponse {
  return {
    id: "doc-1",
    filename: "doc-1.md",
    title: "政策文件",
    category: "general",
    source_url: null,
    doc_metadata: null,
    content_hash: "hash",
    chunk_count: 0,
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
    raw_content: null,
    chunks: [],
    ...overrides,
  };
}

describe("buildPolicyMarkdownContent", () => {
  it("uses raw_content first when available", () => {
    const document = createDocument({
      raw_content: "\n# 原始內容\n\n直接顯示這段\n",
      chunks: [
        {
          id: "chunk-1",
          chunk_index: 0,
          heading: "不應該被使用",
          content: "chunk content",
          token_count: 10,
        },
      ],
    });

    expect(buildPolicyMarkdownContent(document)).toBe(
      "# 原始內容\n\n直接顯示這段",
    );
  });

  it("falls back to sorted chunks when raw_content is empty", () => {
    const document = createDocument({
      raw_content: "   ",
      chunks: [
        {
          id: "chunk-3",
          chunk_index: 2,
          heading: null,
          content: "第三段",
          token_count: 12,
        },
        {
          id: "chunk-1",
          chunk_index: 0,
          heading: "第一節",
          content: "第一段",
          token_count: 12,
        },
        {
          id: "chunk-2",
          chunk_index: 1,
          heading: null,
          content: "第二段",
          token_count: 12,
        },
      ],
    });

    expect(buildPolicyMarkdownContent(document)).toBe(
      "## 第一節\n\n第一段\n\n第二段\n\n第三段",
    );
  });

  it("returns empty fallback text when no raw content and no chunks", () => {
    const document = createDocument({
      raw_content: null,
      chunks: [],
    });

    expect(buildPolicyMarkdownContent(document)).toBe(
      POLICY_MARKDOWN_EMPTY_CONTENT,
    );
  });
});
